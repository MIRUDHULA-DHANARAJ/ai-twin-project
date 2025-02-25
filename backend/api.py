from flask import Flask, jsonify, request
from transformers import pipeline

app = Flask(__name__)

@app.route('/', methods=['GET'])
def root():
    return jsonify({'message': 'Welcome to the AI-Twin API!'})

@app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify({'message': 'Hello from the AI-Twin API!'})

@app.route('/api/summary', methods=['POST'])
def generate_summary():
    data = request.get_json()
    text = data.get('text')
    try:
        summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
        summary_result = summarizer(text, max_length=150, min_length=30, do_sample=False)
        summary = summary_result[0]['summary_text']
        return jsonify({'summary': summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/question', methods=['POST'])
def ask_question():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request. JSON data is required.'}), 400

    question = data.get('question')
    context = data.get('context')

    if not question:
        return jsonify({'error': 'Missing question in request.'}), 400

    if not context:
        return jsonify({'error': 'Missing context in request.'}), 400

    try:
        qa_pipeline = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")
        result = qa_pipeline(question=question, context=context)
        answer = result['answer']
        return jsonify({'answer': answer})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/models', methods=['GET'])
def list_models():
    models = ["distilbert-base-cased-distilled-squad", "sshleifer/distilbart-cnn-12-6"]
    return jsonify({'models': models})
@app.route('/api/feedback', methods=['POST'])
def provide_feedback():
    data = request.get_json()
    feedback = data.get('feedback')
    # Implement logic to store or process feedback
    return jsonify({'message': 'Feedback received: ' + str(feedback)})

if __name__ == '__main__':
    app.run(debug=True)