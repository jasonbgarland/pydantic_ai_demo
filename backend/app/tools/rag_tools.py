"""RAG tools for querying the vector store in agent context."""
import os
from typing import List, Dict, Any
from pathlib import Path
from app.utils.name_utils import normalize_location_name

# Check if OpenAI is available and configured
try:
    from openai import OpenAI
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key and api_key != 'your_openai_api_key_here':
        openai_client = OpenAI(api_key=api_key)
        USE_OPENAI_EMBEDDINGS = True
    else:
        USE_OPENAI_EMBEDDINGS = False
        openai_client = None
except ImportError:
    USE_OPENAI_EMBEDDINGS = False
    openai_client = None

# Try to import chromadb with error handling for numpy compatibility
try:
    import chromadb
    CHROMADB_AVAILABLE = True
except (ImportError, AttributeError) as e:
    CHROMADB_AVAILABLE = False
    print(f"Warning: ChromaDB not available: {e}")
    chromadb = None

def get_chroma_client():
    """Get a Chroma client connection."""
    if not CHROMADB_AVAILABLE:
        return None

    try:
        # Use persistent client with shared volume
        # In Docker: /app/chroma_data
        # Locally: project_root/chroma_data
        chroma_path = Path(__file__).parent.parent / "chroma_data"
        if not chroma_path.exists():
            # Try project root for local development
            chroma_path = Path(__file__).parent.parent.parent.parent / "chroma_data"

        return chromadb.PersistentClient(path=str(chroma_path))
    except Exception as e:
        print(f"Warning: Could not connect to Chroma: {e}")
        return None

def query_world_lore(query: str, location: str = "", max_results: int = 3) -> List[str]:
    """
    Query the vector store for relevant world content.

    Args:
        query: What to search for (e.g., "room description", "treasure")
        location: Optional location context to focus results (accepts any format, will be normalized)
        max_results: Maximum number of results to return

    Returns:
        List of relevant content strings
    """
    if not CHROMADB_AVAILABLE:
        return [f"You are in {location}." if location else "Looking around, you see a mysterious area."]

    try:
        client = get_chroma_client()
        if not client:
            return [f"You are in {location}." if location else "Looking around, you see a mysterious area."]

        collection = client.get_collection("adventure_world")

        # Normalize location name for metadata filtering
        normalized_location = normalize_location_name(location) if location else ""

        # If location is specified, use metadata filtering for better results
        if normalized_location:
            # First try location-specific content with metadata filter
            where_filter = {"location": normalized_location}

            # Use OpenAI embeddings if available
            if USE_OPENAI_EMBEDDINGS and openai_client:
                try:
                    response = openai_client.embeddings.create(
                        input=query,
                        model="text-embedding-3-small"
                    )
                    query_embedding = response.data[0].embedding

                    results = collection.query(
                        query_embeddings=[query_embedding],
                        n_results=max_results,
                        where=where_filter
                    )
                except Exception:
                    # Fall back to text query with filter
                    results = collection.query(
                        query_texts=[query],
                        n_results=max_results,
                        where=where_filter
                    )
            else:
                # Use text query with metadata filter
                results = collection.query(
                    query_texts=[query],
                    n_results=max_results,
                    where=where_filter
                )
        else:
            # No location specified, do regular semantic search
            enhanced_query = query

            if USE_OPENAI_EMBEDDINGS and openai_client:
                try:
                    response = openai_client.embeddings.create(
                        input=enhanced_query,
                        model="text-embedding-3-small"
                    )
                    query_embedding = response.data[0].embedding

                    results = collection.query(
                        query_embeddings=[query_embedding],
                        n_results=max_results
                    )
                except Exception:
                    results = collection.query(
                        query_texts=[enhanced_query],
                        n_results=max_results
                    )
            else:
                results = collection.query(
                    query_texts=[enhanced_query],
                    n_results=max_results
                )

        # Extract the text content
        if results['documents'] and results['documents'][0]:
            return results['documents'][0]
        else:
            return []

    except Exception as e:
        print(f"RAG query error: {e}")
        # Return fallback content if RAG fails
        return [f"A mysterious {location or 'area'} with {query}"]

def get_room_description(room_name: str) -> str:
    """
    Get rich description for a specific room.

    Args:
        room_name: Room name in any format (will be normalized internally)

    Returns:
        Concatenated room descriptions from the vector store
    """
    descriptions = query_world_lore("room description environment", room_name, max_results=5)
    if not descriptions:
        return f"You are in {room_name}."
    
    # Filter and clean description chunks
    cleaned = []
    skip_sections = ['atmospheric details', 'utility benefits', 'discovery opportunities']
    
    for desc in descriptions:
        # Skip chunks that are from special sections (they're more like metadata)
        desc_lower = desc.lower()
        if any(section in desc_lower for section in skip_sections):
            continue
            
        # Remove lines starting with # (markdown headers) or - (bullet points from those sections)
        lines = []
        for line in desc.split('\n'):
            stripped = line.strip()
            # Skip markdown headers
            if stripped.startswith('#'):
                continue
            # Skip bullet points (likely from atmospheric/utility sections)
            if stripped.startswith('-'):
                continue
            # Skip metadata lines
            if stripped.startswith('##') or ':**' in line:
                continue
            if stripped:
                lines.append(line)
        
        cleaned_text = '\n'.join(lines).strip()
        if cleaned_text and len(cleaned_text) > 30:  # Only include substantial content
            cleaned.append(cleaned_text)
    
    # Return up to 2 main descriptive paragraphs
    return " ".join(cleaned[:2]) if cleaned else f"You are in {room_name}."

def find_items_in_location(location: str) -> List[str]:
    """Find items available in a specific location by parsing room metadata.
    
    Returns a list of item names (e.g., ['rope', 'torch', 'leather_pack'])
    """
    # First try to parse from the markdown file directly
    normalized_location = normalize_location_name(location)
    world_data_path = Path(__file__).parent.parent / "world_data" / "rooms"
    
    # Try to find the room file
    for room_file in world_data_path.glob("*.md"):
        with open(room_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Check if this is the right room by looking for Location: header
            for line in content.split('\n'):
                if line.startswith('## Location:'):
                    file_location = line.replace('## Location:', '').strip()
                    if normalize_location_name(file_location) == normalized_location:
                        # Found the right room, now extract items
                        for item_line in content.split('\n'):
                            if item_line.startswith('## Items:'):
                                items_str = item_line.replace('## Items:', '').strip()
                                if items_str:
                                    # Parse comma-separated items
                                    return [item.strip() for item in items_str.split(',')]
                                return []
    
    # Fallback to RAG query if file parsing fails
    items = query_world_lore("items objects pickup treasure", location, max_results=3)
    return items

def get_environmental_details(location: str, aspect: str) -> str:
    """Get specific environmental details about a location."""
    details = query_world_lore(f"{aspect} details features", location, max_results=2)
    return " ".join(details) if details else f"Nothing particularly notable about {aspect}."