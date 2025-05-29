import os
from datetime import datetime, timedelta
from services.BaseService import BaseService
from services.ModelService import ModelService
from dao.PhaseDetectionDAO import PhaseDetectionDAO
from dao.FrameDetectionDAO import FrameDetectionDAO
from models.PhaseDetection import PhaseDetection

from config.config import Config


class PhaseDetectionService(BaseService):
    def __init__(self):
        super().__init__()
        self.dao = PhaseDetectionDAO()
        self.model_service = ModelService()
        self.result_dao = FrameDetectionDAO()
    
    def create(self, detection):
        detection_id = self.dao.insert(detection)
        if detection_id:
            detection.id = detection_id
            return detection
        raise Exception("Failed to create detection")
    
    def update(self, id, data):
       
        existing = self.dao.find_by_id(id)
        if not existing:
            raise ValueError(f"Detection with ID {id} not found")
        
        # Update fields
        if 'modelId' in data:
            model = self.model_service.get_by_id(data['modelId'])
            existing.model = model
        
        if 'description' in data:
            existing.description = data['description']
        
        if 'timeDetect' in data:
            existing.timeDetect = datetime.strptime(data['timeDetect'], '%Y-%m-%d %H:%M:%S')
        
        # Update in database
        if self.dao.update(existing):
            return existing
        
        raise Exception("Failed to update detection")
    
    def delete(self, id):
        existing = self.dao.find_by_id(id)
        if not existing:
            raise ValueError(f"Detection with ID {id} not found")
        
        # Delete associated images if configured
        if hasattr(Config, 'DELETE_IMAGES_ON_DETECTION_DELETE') and Config.DELETE_IMAGES_ON_DETECTION_DELETE:
            for result in existing.result:
                if result.imageUrl:
                    self._delete_image_file(result.imageUrl)
        
        # Delete (will cascade delete result detections)
        if self.dao.delete(id):
            return True
        
        raise Exception("Failed to delete detection")
    
    def get_by_id(self, id):
      
        detection = self.dao.find_by_id(id)
        if not detection:
            raise ValueError(f"Detection with ID {id} not found")
        return detection
    
    def get_all(self):
        
        return self.dao.find_all()
    
  
 