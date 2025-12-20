from flask import Flask, jsonify
from flask_cors import CORS
from routes.query_routes import query_bp
from routes.health_routes import health_bp

def create_app():
    app = Flask(__name__)
    CORS(app, 
         resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"]}},
         supports_credentials=True)
    
    # Root route
    @app.route('/')
    def root():
        return jsonify({
            "message": "RAG Chatbot API",
            "endpoints": {
                "health": "/api/health",
                "methods": "/api/methods",
                "query": "/api/query (POST)"
            }
        }), 200
    
    # Register blueprints
    app.register_blueprint(health_bp, url_prefix='/api')
    app.register_blueprint(query_bp, url_prefix='/api')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)

