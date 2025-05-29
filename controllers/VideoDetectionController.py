import json
from flask import request, jsonify
from models.Detection import Detection
from datetime import datetime

from services import VideoDetectionService
from services.DetectionService import DetectionService
from services.FileStorageService import FileStorageService
from services.ModelService import ModelService

class VideoDetectionController:
    def __init__(self):
        self.model_service = ModelService()
        self.video_detection_service = VideoDetectionService()
        self.file_storage_service = FileStorageService()
        self.detection_service = DetectionService()
        
    def detect_video(self):
        try:
            if 'video' not in request.files:
                return jsonify({'error': 'Video file is required'}), 400    
            if 'detection' not in request.form:
                return jsonify({'error': 'Detection data is required'}), 400
            try:
                detection_data = json.loads(request.form.get('detection'))
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid detection data format'}), 400
            
            print(f"Received detection data: {detection_data}")  # Debugging line
            # Tạo đối tượng Detection từ dict
            detection = Detection.from_dict(detection_data)
            
            
            if not detection.model or not hasattr(detection.model, 'id'):
                return jsonify({'error': 'Model ID is required'}), 400
                
            
            try:
                model = self.model_service.get_by_id(detection.model.id)
                detection.model = model
            except Exception as e:
                return jsonify({'error': f'Invalid model_id: {str(e)}'}), 404
            
            # Save video file
            try:
                video_path, video_url = self.file_storage_service.save_video(
                    request.files['video'], 
                    prefix='detection'
                )
                detection.videoUrl = video_url  
            except Exception as e:
                return jsonify({'error': f'Failed to save video: {str(e)}'}), 500
            if detection.timeDetect is None:
                detection.timeDetect = datetime.now()
            
            
            # print(f"Detection object: {detection.to_dict()}")  # Debugging line
            # Process video với detection object
            result = self.video_detection_service.process_video(
                detection=detection,
                video_path=video_path
            )
            
         
            print(f"Detection result: {result.to_dict()}")  # Debugging line
            
            return jsonify(result.to_dict()), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def register_routes(self, app):
        """Register routes with Flask app"""
        app.add_url_rule('/api/detection/video', 'detect_video', 
                         self.detect_video, methods=['POST'])