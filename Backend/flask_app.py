from flask import Flask, request, jsonify
from flask_cors import CORS
from RAG import process_chat_text
from Query import query_database, generate_answer

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/api/process-text', methods=['POST'])
def process_text():
    try:
        # Get the text from the request body
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400

        text = data['text']
        
        # Process the text using RAG
        result = process_chat_text(text)
        
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({'error': 'No question provided'}), 400

        question = data['question']
        
        # Get relevant context from database
        relevant_chunks = query_database(question)
        # print(relevant_chunks)
        if relevant_chunks is None:
            return jsonify({'error': 'Error querying database'}), 500
            
        context = "\n\n".join(relevant_chunks)
        print(context)
        # Generate answer using the context
        answer = generate_answer(question, context)
        print(answer)
        return jsonify({'answer': answer})

    except Exception as e:
        print(f"Error {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

