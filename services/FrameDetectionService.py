from services.BaseService import BaseService
from dao.FrameDetectionDAO import FrameDetectionDAO
from dao.PhaseDetectionDAO import PhaseDetectionDAO
from dao.BoundingBoxDetectionDAO import BoundingBoxDetectionDAO
from models.FrameDetection import FrameDetection
from models.BoundingBoxDetection import BoundingBoxDetection
from datetime import datetime


class FrameDetectionService(BaseService):
    def __init__(self):
        super().__init__()
        self.dao = FrameDetectionDAO()
        
        

    def create(self, frame_detection):
        frame_detection= self.dao.insert(frame_detection)
        if frame_detection:
            return frame_detection
        raise Exception("Failed to create frame detection")

    def update(self, frame_detection):
        existing = self.dao.find_by_id(frame_detection.id)
        if not existing:
            raise ValueError(f"FrameDetection with ID {frame_detection.id} not found")

        if 'imageUrl' in frame_detection:
            existing.imageUrl = frame_detection['imageUrl']

        if 'detectionId' in frame_detection:
            detection = self.detection_dao.find_by_id(frame_detection['detectionId'])
            if not detection:
                raise ValueError(f"Detection with ID {frame_detection['detectionId']} not found")
            existing.detection = detection

        if 'listFraud' in frame_detection:
            existing.listFraud = frame_detection['listFraud']

       

        if self.dao.update(existing):
            return existing

        raise Exception("Failed to update result detection")
    
    def delete(self, id):
        existing = self.dao.find_by_id(id)
        if not existing:
            raise ValueError(f"FrameDetection with ID {id} not found")
        
        if self.dao.delete(id):
            return True
        raise Exception("Failed to delete result detection")
    
    def get_by_id(self, id):
        frame_detection = self.dao.find_by_id(id)
        if not frame_detection:
            raise ValueError(f"FrameDetection with ID {id} not found")
        return frame_detection
    
    def get_all(self):
        return self.dao.find_all()
    
   
  
