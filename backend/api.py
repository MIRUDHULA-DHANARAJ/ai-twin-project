from flask import Flask, jsonify, request
from transformers import pipeline
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@app.route('/', methods=['GET'])
def root():
    logger.info("Received GET request to /")
    return jsonify({'message': 'Welcome to the AI-Twin API!'})

@app.route('/api/hello', methods=['GET'])
def hello():
    logger.info("Received GET request to /api/hello")
    return jsonify({'message': 'Hello from the AI-Twin API!'})

@app.route('/api/summary', methods=['POST'])
def generate_summary():
    data = request.get_json()
    logger.info(f"Received POST request to /api/summary: {data}")
    if not data:
        logger.warning("Invalid request: No JSON data provided.")
        return jsonify({'error': 'Invalid request. JSON data is required.'}), 400

    text = data.get('text')
    if not text:
        logger.warning("Invalid request: Missing 'text' in request.")
        return jsonify({'error': 'Missing text in request.'}), 400

    try:
        summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
        summary_result = summarizer(text, max_length=150, min_length=30, do_sample=False)
        summary = summary_result[0]['summary_text']
        logger.info(f"Sending /api/summary response: {summary}")
        return jsonify({'summary': summary})
    except Exception as e:
        logger.error(f"Error processing /api/summary request: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/question', methods=['POST'])
def ask_question():
    data = request.get_json()
    logger.info(f"Received POST request to /api/question: {data}")
    if not data:
        logger.warning("Invalid request: No JSON data provided.")
        return jsonify({'error': 'Invalid request. JSON data is required.'}), 400

    question = data.get('question')
    context = data.get('context')

    if not question:
        logger.warning("Invalid request: Missing 'question' in request.")
        return jsonify({'error': 'Missing question in request.'}), 400

    if not context:
        logger.warning("Invalid request: Missing 'context' in request.")
        return jsonify({'error': 'Missing context in request.'}), 400

    try:
        qa_pipeline = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")
        result = qa_pipeline(question=question, context=context)
        answer = result['answer']
        logger.info(f"Sending /api/question response: {answer}")
        return jsonify({'answer': answer})
    except Exception as e:
        logger.error(f"Error processing /api/question request: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/models', methods=['GET'])
def list_models():
    logger.info("Received GET request to /api/models")
    models = ["distilbert-base-cased-distilled-squad", "sshleifer/distilbart-cnn-12-6"]
    logger.info(f"Sending /api/models response: {models}")
    return jsonify({'models': models})

@app.route('/api/feedback', methods=['POST'])
def provide_feedback():
    data = request.get_json()
    logger.info(f"Received POST request to /api/feedback: {data}")
    if not data:
        logger.warning("Invalid request: No JSON data provided.")
        return jsonify({'error': 'Invalid request. JSON data is required.'}), 400

    feedback = data.get('feedback')
    if not feedback:
        logger.warning("Invalid request: Missing 'feedback' in request.")
        return jsonify({'error': 'Missing feedback in request.'}), 400
    try:
        logger.info(f"Sending /api/feedback response: Feedback received: {feedback}")
        return jsonify({'message': 'Feedback received: ' + str(feedback)})
    except Exception as e:
        logger.error(f"Error processing /api/feedback request: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)