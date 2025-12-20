from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "RAG Chatbot API"}), 200

@health_bp.route('/methods', methods=['GET'])
def get_methods():
    return jsonify({
        "methods": [
            {"id": 1, "name": "Simple Vector RAG", "description": "FAISS vector similarity"},
            {"id": 2, "name": "Parent-Child RAG", "description": "Precise child + complete parent"},
            {"id": 3, "name": "Agentic RAG", "description": "Multi-tool agent with entropy analysis"}
        ]
    }), 200

