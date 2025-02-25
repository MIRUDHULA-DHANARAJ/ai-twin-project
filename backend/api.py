from flask import Flask, jsonify, request

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
    # Implement AI summary logic here
    summary = "This is a placeholder summary. Text received: " + str(text) #added text received to help with testing.
    return jsonify({'summary': summary})

@app.route('/api/question', methods=['POST'])
def ask_question():
    data = request.get_json()
    question = data.get('question')
    # Implement AI question-answering logic here
    answer = "This is a placeholder answer. Question received: " + str(question) #added question received to help with testing.
    return jsonify({'answer': answer})

@app.route('/api/models', methods=['GET'])
def list_models():
    # Implement logic to list available AI models
    models = ["model1", "model2", "model3"]  # Placeholder list
    return jsonify({'models': models})

@app.route('/api/feedback', methods=['POST'])
def provide_feedback():
    data = request.get_json()
    feedback = data.get('feedback')
    # Implement logic to store or process feedback
    return jsonify({'message': 'Feedback received: ' + str(feedback)}) #added feedback received to help with testing.

if __name__ == '__main__':
    app.run(debug=True)