"""
Seed world data into Chroma vector database for RAG-powered room descriptions.

This script processes room and item descriptions from markdown files and stores them
in Chroma with embeddings for semantic search by the RoomDescriptor agent.
"""
import os
import re
from pathlib import Path
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings
import openai
from markdown_it import MarkdownIt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def parse_markdown_file(file_path: Path) -> Dict[str, Any]:
    """Parse a markdown file into structured data using markdown-it-py."""
    content = file_path.read_text()
    md = MarkdownIt()

    # Parse markdown into tokens
    tokens = md.parse(content)

    # Extract metadata from structured format
    metadata = {}
    lines = content.split('\n')

    # Find title (first heading)
    title = ""
    for token in tokens:
        if token.type == 'heading_open' and token.tag == 'h1':
            # Find the corresponding inline token
            next_token_idx = tokens.index(token) + 1
            if next_token_idx < len(tokens) and tokens[next_token_idx].type == 'inline':
                title = tokens[next_token_idx].content.strip()
                break

    # Extract metadata from bold key-value pairs and structured headers
    in_metadata_section = True
    content_start_line = 0

    for i, line in enumerate(lines):
        if line.startswith('# '):
            title = line[2:].strip()
            continue

        # Look for metadata in **Key:** value format
        if in_metadata_section and line.startswith('**') and ':**' in line:
            key_value = line.replace('**', '').split(':', 1)
            if len(key_value) == 2:
                key = key_value[0].strip().lower().replace(' ', '_')
                value = key_value[1].strip()
                metadata[key] = value
        # Also look for ## Key: value format
        elif line.startswith('## ') and ':' in line:
            key, value = line[3:].split(':', 1)
            metadata[key.strip().lower().replace(' ', '_')] = value.strip()
        elif in_metadata_section and line.strip() == '' and i > 0:
            # Empty line after metadata, content starts next
            content_start_line = i + 1
        elif in_metadata_section and not line.startswith(('**', '## ')) and line.strip():
            # Non-metadata content found, stop looking for metadata
            in_metadata_section = False
            content_start_line = i
            break

    # Extract main content
    main_content = '\n'.join(lines[content_start_line:])

    # Smart chunking by headings using markdown tokens
    chunks = smart_chunk_by_structure(tokens, content)

    # Add derived metadata
    metadata['title'] = title or file_path.stem
    metadata['file_type'] = 'room' if 'rooms' in str(file_path) else 'item'
    metadata['file_name'] = file_path.stem
    metadata['location'] = file_path.stem

    return {
        'metadata': metadata,
        'content': main_content,
        'chunks': chunks,
        'tokens': tokens
    }

def smart_chunk_by_structure(tokens: List, content: str, max_chunk_size: int = 500) -> List[Dict[str, Any]]:
    """Smart chunking that preserves heading structure using markdown tokens."""
    chunks = []

    # Find headings in tokens
    headings = []
    for i, token in enumerate(tokens):
        if token.type == 'heading_open' and token.tag in ['h2', 'h3', 'h4']:
            # Get heading text from next inline token
            heading_text = ""
            if i + 1 < len(tokens) and tokens[i + 1].type == 'inline':
                heading_text = tokens[i + 1].content
            headings.append({
                'level': int(token.tag[1]),  # h2 -> 2, h3 -> 3, etc.
                'text': heading_text,
                'line': token.map[0] if token.map else 0
            })

    # If no headings found, use simple paragraph chunking
    if not headings:
        return simple_chunk_content(content, max_chunk_size)

    # Split content by headings
    lines = content.split('\n')
    current_chunk = ""
    current_heading = ""

    for line in lines:
        # Check if this line is a heading
        is_heading = False
        for heading in headings:
            if line.strip().startswith('#') and heading['text'] in line:
                is_heading = True
                # Save previous chunk
                if current_chunk.strip():
                    chunks.append({
                        'heading': current_heading,
                        'content': current_chunk.strip(),
                        'type': 'section',
                        'size': len(current_chunk)
                    })
                current_heading = heading['text']
                current_chunk = ""
                break

        if not is_heading:
            # Add to current chunk, but check size
            if len(current_chunk + line) > max_chunk_size and current_chunk:
                # Split the chunk
                chunks.append({
                    'heading': current_heading,
                    'content': current_chunk.strip(),
                    'type': 'section',
                    'size': len(current_chunk)
                })
                current_chunk = line + '\n'
            else:
                current_chunk += line + '\n'

    # Add final chunk
    if current_chunk.strip():
        chunks.append({
            'heading': current_heading,
            'content': current_chunk.strip(),
            'type': 'section',
            'size': len(current_chunk)
        })

    return chunks

def simple_chunk_content(content: str, max_chunk_size: int = 500) -> List[Dict[str, Any]]:
    """Simple paragraph-based chunking fallback."""
    chunks = []
    paragraphs = content.split('\n\n')
    current_chunk = ""

    for paragraph in paragraphs:
        if len(current_chunk + paragraph) > max_chunk_size and current_chunk:
            chunks.append({
                'heading': '',
                'content': current_chunk.strip(),
                'type': 'paragraph',
                'size': len(current_chunk)
            })
            current_chunk = paragraph + '\n\n'
        else:
            current_chunk += paragraph + '\n\n'

    if current_chunk.strip():
        chunks.append({
            'heading': '',
            'content': current_chunk.strip(),
            'type': 'paragraph',
            'size': len(current_chunk)
        })

    return chunks

def chunk_content(content: str, max_chunk_size: int = 500) -> List[str]:
    """Split content into chunks suitable for embedding."""
    # Split by paragraphs first
    paragraphs = content.split('\n\n')
    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        # If adding this paragraph would exceed chunk size, save current chunk
        if len(current_chunk) + len(paragraph) > max_chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = paragraph
        else:
            current_chunk += "\n\n" + paragraph if current_chunk else paragraph

    # Add the final chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Get embeddings for text chunks using OpenAI."""
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    response = client.embeddings.create(
        input=texts,
        model="text-embedding-3-small"
    )

    return [data.embedding for data in response.data]

def setup_chroma_client() -> chromadb.Client:
    """Initialize Chroma client with persistent storage."""
    # Use persistent client that matches rag_tools.py
    # Path: backend/app/chroma_data (same as used by the app)
    chroma_path = Path(__file__).parent / "app" / "chroma_data"

    print(f"Using persistent Chroma client at: {chroma_path}")
    client = chromadb.PersistentClient(path=str(chroma_path))
    return client

def seed_world_data():
    """Main function to seed world data into Chroma."""
    print("🌍 Starting world data seeding...")

    # Check for OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key == 'your_openai_api_key_here':
        print("❌ OPENAI_API_KEY not found or not configured.")
        print("   Please set a real OpenAI API key in your .env file to generate embeddings.")
        print("   For now, seeding with placeholder embeddings...")
        use_real_embeddings = False
    else:
        use_real_embeddings = True

    # Setup Chroma client
    client = setup_chroma_client()

    # Create or get collection
    collection_name = "adventure_world"
    try:
        # Delete existing collection if it exists to avoid dimension mismatch
        try:
            client.delete_collection(collection_name)
            print(f"Deleted existing collection: {collection_name}")
        except:
            pass  # Collection might not exist

        collection = client.create_collection(
            name=collection_name,
            metadata={"description": "Adventure game world descriptions and items"}
        )
        print(f"Created new collection: {collection_name}")
    except Exception as e:
        print(f"Error setting up collection: {e}")
        return

    # Process all markdown files
    world_data_path = Path(__file__).parent / "app" / "world_data"
    all_chunks = []
    all_metadata = []
    all_ids = []

    chunk_id = 0

    # Process rooms
    rooms_path = world_data_path / "rooms"
    if rooms_path.exists():
        for md_file in rooms_path.glob("*.md"):
            print(f"Processing room: {md_file.name}")
            data = parse_markdown_file(md_file)

            # Use new chunk structure
            chunks = data['chunks']

            for i, chunk_data in enumerate(chunks):
                chunk_text = chunk_data['content']
                all_chunks.append(chunk_text)
                metadata = {
                    **data['metadata'],
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'file_type': 'room',
                    'heading': chunk_data.get('heading', ''),
                    'chunk_type': chunk_data.get('type', 'section')
                }
                all_metadata.append(metadata)
                all_ids.append(f"room_{data['metadata']['file_name']}_chunk_{i}")
                chunk_id += 1

    # Process items
    items_path = world_data_path / "items"
    if items_path.exists():
        for md_file in items_path.glob("*.md"):
            print(f"Processing item: {md_file.name}")
            data = parse_markdown_file(md_file)

            # Use new chunk structure
            chunks = data['chunks']

            for i, chunk_data in enumerate(chunks):
                chunk_text = chunk_data['content']
                all_chunks.append(chunk_text)
                metadata = {
                    **data['metadata'],
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'file_type': 'item',
                    'heading': chunk_data.get('heading', ''),
                    'chunk_type': chunk_data.get('type', 'section')
                }
                all_metadata.append(metadata)
                all_ids.append(f"item_{data['metadata']['file_name']}_chunk_{i}")
                chunk_id += 1

    if not all_chunks:
        print("❌ No markdown files found to process.")
        return

    print(f"📄 Processed {len(all_chunks)} content chunks")

    # Get embeddings
    if use_real_embeddings:
        print("🔮 Generating embeddings with OpenAI...")
        embeddings = get_embeddings(all_chunks)
    else:
        print("🔮 Generating placeholder embeddings...")
        # Create dummy embeddings for testing (384 dimensions for all-MiniLM-L6-v2, Chroma's default)
        embeddings = [[0.0] * 384 for _ in all_chunks]

    # Store in Chroma
    print("💾 Storing in Chroma...")
    collection.add(
        documents=all_chunks,
        embeddings=embeddings,
        metadatas=all_metadata,
        ids=all_ids
    )

    print(f"✅ Successfully seeded {len(all_chunks)} chunks into Chroma collection '{collection_name}'")

    # Test with a query
    try:
        print("🔍 Testing query functionality...")
        # Use OpenAI embeddings for query to match the storage
        if use_real_embeddings:
            from openai import OpenAI
            openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

            test_query = "crystal treasury room description"
            response = openai_client.embeddings.create(
                input=test_query,
                model="text-embedding-3-small"
            )
            query_embedding = response.data[0].embedding

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=3
            )
        else:
            # Use text query for placeholder embeddings
            results = collection.query(
                query_texts=["crystal treasury room description"],
                n_results=3
            )

        print(f"Test query returned {len(results['documents'][0])} results:")
        for i, doc in enumerate(results['documents'][0][:2]):  # Show first 2 results
            print(f"  {i+1}. {doc[:100]}...")
    except Exception as e:
        print(f"Query test failed: {e}")
        print("✅ Data was still seeded successfully!")

if __name__ == "__main__":
    seed_world_data()