import os
from dotenv import load_dotenv
import chromadb
from sklearn.metrics.pairwise import cosine_similarity
import tiktoken
import time
import openai

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize models and clients
encoder = tiktoken.get_encoding("cl100k_base")

def init_chroma_client(max_retries=3, retry_delay=2):
    for attempt in range(max_retries):
        try:
            # Use standard ChromaDB client instead of persistent client
            client = chromadb.Client()
            # Test the connection by getting collections
            client.list_collections()
            return client
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Failed to connect to ChromaDB after {max_retries} attempts.")
                print(f"Error: {str(e)}")
                raise
            print(f"Attempt {attempt + 1} failed. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

chroma_client = init_chroma_client()

def count_tokens(text):
    return len(encoder.encode(text))

def compute_embeddings_for_sentences(sentences):
    embeddings = []
    for sentence in sentences:
        response = openai.embeddings.create(
            model="text-embedding-3-small",  # or "text-embedding-ada-002"
            input=sentence
        )
        embeddings.append(response.data[0].embedding)
    return embeddings

def semantic_chunker(text, threshold=0.75, max_tokens=512):
    sentences = text.split('. ')
    embeddings = compute_embeddings_for_sentences(sentences)
    
    chunks = []
    current_chunk = [sentences[0]]
    current_chunk_tokens = count_tokens(sentences[0])
    
    for i in range(1, len(sentences)):
        sentence_tokens = count_tokens(sentences[i])
        similarity = cosine_similarity([embeddings[i-1]], [embeddings[i]])[0][0]
        
        if similarity < threshold or (current_chunk_tokens + sentence_tokens > max_tokens):
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentences[i]]
            current_chunk_tokens = sentence_tokens
        else:
            current_chunk.append(sentences[i])
            current_chunk_tokens += sentence_tokens
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

def store_in_chromadb(chunks):
    from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
    
    # Add logging
    print(f"Attempting to store {len(chunks)} chunks in ChromaDB")
    
    embedding_function = OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="text-embedding-3-small"
    )
    
    # First, check if collection exists
    try:
        collection = chroma_client.get_collection(name="ChatHistory")
        print("Found existing ChatHistory collection")
    except Exception as e:
        print("Collection doesn't exist, creating new one")
        collection = chroma_client.create_collection(
            name="ChatHistory",
            embedding_function=embedding_function
        )
    
    chunk_ids = [f"chunk_{i}" for i in range(len(chunks))]
    collection.add(
        documents=chunks,
        ids=chunk_ids,
        metadatas=[{"timestamp": "current_time"} for _ in chunks]
    )
    
    # Verify storage by counting documents
    count = collection.count()
    print(f"Successfully stored chunks. Collection now contains {count} documents")

def process_chat_text(text):
    """Main function to process incoming chat text"""
    try:
        # Add logging
        print("Starting chat text processing")
        
        chunks = semantic_chunker(text)
        print(f"Created {len(chunks)} semantic chunks")
        
        store_in_chromadb(chunks)
        
        return {"status": "success", "num_chunks": len(chunks)}
    except Exception as e:
        print(f"Error processing chat text: {str(e)}")
        return {"status": "error", "message": str(e)}

