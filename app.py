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




if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'videos'), exist_ok=True)
    
    
    
    # Run app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=Config.DEBUG
    )