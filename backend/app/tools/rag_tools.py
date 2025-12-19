"""RAG tools for querying the vector store in agent context."""
import os
import chromadb
from typing import List, Dict, Any
from pathlib import Path

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

def get_chroma_client():
    """Get a Chroma client connection."""
    try:
        # Try HTTP client first
        client = chromadb.HttpClient(host="localhost", port=8000)
        client.list_collections()  # Test connection
        return client
    except Exception:
        # Fall back to persistent client - use the project root chroma_data
        chroma_path = Path(__file__).parent.parent.parent.parent / "chroma_data"
        return chromadb.PersistentClient(path=str(chroma_path))

def query_world_lore(query: str, location: str = "", max_results: int = 3) -> List[str]:
    """
    Query the vector store for relevant world content.
    
    Args:
        query: What to search for (e.g., "room description", "treasure")
        location: Optional location context to focus results
        max_results: Maximum number of results to return
    
    Returns:
        List of relevant content strings
    """
    try:
        client = get_chroma_client()
        collection = client.get_collection("adventure_world")
        
        # If location is specified, use metadata filtering for better results
        if location:
            # First try location-specific content with metadata filter
            where_filter = {"location": location}
            
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
    """Get rich description for a specific room."""
    descriptions = query_world_lore("room description environment", room_name, max_results=3)
    return " ".join(descriptions) if descriptions else f"You are in {room_name}."

def find_items_in_location(location: str) -> List[str]:
    """Find items available in a specific location."""
    items = query_world_lore("items objects pickup treasure", location, max_results=3)
    return items

def get_environmental_details(location: str, aspect: str) -> str:
    """Get specific environmental details about a location."""
    details = query_world_lore(f"{aspect} details features", location, max_results=2)
    return " ".join(details) if details else f"Nothing particularly notable about {aspect}."