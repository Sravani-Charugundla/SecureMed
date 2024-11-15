import chromadb
from dotenv import load_dotenv
from chromadb.utils.embedding_functions.openai_embedding_function import OpenAIEmbeddingFunction
import openai
import os
from groq import Groq

# Load environment variables
load_dotenv()

# Create a regular in-memory client
chroma_client = chromadb.Client()

# Initialize OpenAI embedding function once
openai_ef = OpenAIEmbeddingFunction(
    api_key=os.getenv('OPENAI_API_KEY'),
    model_name="text-embedding-3-small"
)

def query_database(query_text, num_chunks=5):
    try:
        collection = chroma_client.get_collection(name="ChatHistory", embedding_function=openai_ef)
       
        results = collection.query(
            query_texts=[query_text],
            n_results=num_chunks,
            include=["documents", "metadatas", "distances"]
        )
        
        return results['documents'][0]
    except Exception as e:
        print(f"Error querying database: {e}")
        return None

def generate_answer(question, context):
    prompt = f"""Answer the question based on the provided context. If the answer cannot be found in the context, respond with "I cannot answer this question based on the provided context."
                
                Context: {context}
                Question: {question}
                Answer:"""
    
    client = Groq()
    
    completion = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8,
        max_tokens=1024,
        top_p=1,
        stream=False  # Changed to False for simpler handling
    )
    
    return completion.choices[0].message.content.strip()

if __name__ == "__main__":
    question = "your question here"
    relevant_chunks = query_database(question)
    context = "\n\n".join(relevant_chunks)
    answer = generate_answer(question, context)
    print(answer)

 
