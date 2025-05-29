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
        self.phase_detection_dao = PhaseDetectionDAO()
        self.bbox_dao = BoundingBoxDetectionDAO()

    def create(self, frame_detection):
        frame_detection_id = self.dao.insert(frame_detection)
        if frame_detection_id:
            frame_detection.id = frame_detection_id
            return frame_detection
        raise Exception("Failed to create frame detection")

    def update(self, id, data):
        existing = self.dao.find_by_id(id)
        if not existing:
            raise ValueError(f"FrameDetection with ID {id} not found")

        if 'imageUrl' in data:
            existing.imageUrl = data['imageUrl']
        
        if 'detectionId' in data:
            detection = self.detection_dao.find_by_id(data['detectionId'])
            if not detection:
                raise ValueError(f"Detection with ID {data['detectionId']} not found")
            existing.detection = detection
        
        if 'listFraud' in data:
            existing.listFraud = data['listFraud']

        # Optional: update bounding boxes
        if 'listBoundingBoxDetection' in data:
            # Delete all existing bounding boxes
            self.bbox_dao.delete_by_frame_detection_id(id)

            existing.listBoundingBoxDetection = []
            for bbox_data in data['listBoundingBoxDetection']:
                bbox = BoundingBoxDetection.from_dict(bbox_data)
                bbox.frameDetection = existing
                self.bbox_dao.insert(bbox)
                existing.listBoundingBoxDetection.append(bbox)

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
    
    def get_by_detection_id(self, detection_id):
        return self.dao.find_by_detection_id(detection_id)
    
    def get_by_confidence_threshold(self, min_confidence):
        return self.dao.find_by_confidence_threshold(min_confidence)
