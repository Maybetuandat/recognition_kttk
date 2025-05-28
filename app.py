import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from controllers.VideoDetectionController import VideoDetectionController
from controllers.ModelController import ModelController
from config.config import Config

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join(Config.BASE_DIR, 'uploads')

# Enable CORS
CORS(app)

# Initialize Config
Config.init_app(app)

# Initialize controllers
video_detection_controller = VideoDetectionController()
model_controller = ModelController()

# Register routes
video_detection_controller.register_routes(app)
model_controller.register_routes(app)

# Static file routes for uploaded content
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/uploads/frames/<path:filename>')
def uploaded_frame(filename):
    """Serve uploaded frame images"""
    frames_path = os.path.join(app.config['UPLOAD_FOLDER'], 'frames')
    return send_from_directory(frames_path, filename)

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'Video Detection API',
        'version': '1.0.0'
    })

# Error handlers
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        'error': 'File too large. Maximum size is 500MB'
    }), 413

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'videos'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'frames'), exist_ok=True)
    os.makedirs(os.path.join(Config.BASE_DIR, 'static', 'visualizations'), exist_ok=True)
    
    # Run app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.DEBUG
    )