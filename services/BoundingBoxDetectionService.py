from services.BaseService import BaseService
from dao.BoundingBoxDetectionDAO import BoundingBoxDetectionDAO
from models.BoundingBoxDetection import BoundingBoxDetection
from datetime import datetime


class BoundingBoxDetectionService(BaseService):
    def __init__(self):
        super().__init__()
        self.dao = BoundingBoxDetectionDAO()

    def create(self, bounding_box_detection):
        bbox = self.dao.insert(bounding_box_detection)

        if bbox:
            return bbox
        raise Exception("Failed to create bounding box detection")
    
    def update(self, boundingbox):
        existing = self.dao.find_by_id(boundingbox.id)
        if not existing:
            raise ValueError(f"BoundingBoxDetection with ID {boundingbox.id} not found")

        for field in ['fraudLabel', 'frameDetection', 'xCenter', 'yCenter', 'width', 'height', 'confidence']:
            if field in boundingbox:
                setattr(existing, field, boundingbox[field])

        if self.dao.update(existing):
            return existing
        raise Exception("Failed to update bounding box detection")
    
    def delete(self, id):
        existing = self.dao.find_by_id(id)
        if not existing:
            raise ValueError(f"BoundingBoxDetection with ID {id} not found")
        
        if self.dao.delete(id):
            return True
        raise Exception("Failed to delete bounding box detection")
    
    def get_by_id(self, id):
        bbox = self.dao.find_by_id(id)
        if not bbox:
            raise ValueError(f"BoundingBoxDetection with ID {id} not found")
        return bbox
    
    def get_all(self):
        return self.dao.find_all()
    
   
