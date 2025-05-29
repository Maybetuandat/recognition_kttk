from dao.BaseDAO import BaseDAO

from dao.BoundingBoxDetectionDAO import BoundingBoxDetectionDAO
from models.FrameDetection import FrameDetection

from models.FraudLabel import FraudLabel


class FrameDetectionDAO(BaseDAO):
    def __init__(self):
        super().__init__()
        self.bounding_box_dao = BoundingBoxDetectionDAO()
        self.create_table()
    
    def create_table(self):
        
        query = """
        CREATE TABLE IF NOT EXISTS frame_detection (
            id INT AUTO_INCREMENT PRIMARY KEY,
            detection_id INT,
            image_url VARCHAR(500),
            FOREIGN KEY (detection_id) REFERENCES detection(id) ON DELETE CASCADE
        )
        """
        self.execute_query(query)
    
    def insert(self, frame_detection):
        
        query = """
        INSERT INTO frame_detection 
        (detection_id, image_url)
        VALUES (%s, %s)
        """
        params = (
            frame_detection.detection.id if frame_detection.detection else None,
            frame_detection.imageUrl
        )
        
        return self.execute_query(query, params)
    def update(self, frame_detection):
        """Update an existing result detection record"""
        query = """
        UPDATE frame_detection
        SET detection_id = %s, image_url = %s, bbox_x = %s, bbox_y = %s, 
            bbox_width = %s, bbox_height = %s, confidence = %s
        WHERE id = %s
        """
        params = (
            frame_detection.detection.id if frame_detection.detection else None,
            frame_detection.imageUrl,
            frame_detection.bboxX,
            frame_detection.bboxY,
            frame_detection.bboxWidth,
            frame_detection.bboxHeight,
            frame_detection.confidence,
            frame_detection.id
        )
        
        # Update main record
        success = self.execute_query(query, params)
        
       
        
        return success
    
    def delete(self, id):
        """Delete a result detection record by id"""
        # Relationships will be auto-deleted due to CASCADE
        query = "DELETE FROM frame_detection WHERE id = %s"
        return self.execute_query(query, (id,))
    
    def delete_by_detection_id(self, detection_id):
        """Delete all result detections for a specific detection"""
        query = "DELETE FROM frame_detection WHERE detection_id = %s"
        return self.execute_query(query, (detection_id,))
    
    def find_by_id(self, id):
        """Find a result detection record by id"""
        query = "SELECT * FROM frame_detection WHERE id = %s"
        result = self.fetch_one(query, (id,))
        
        if result:
            frame_detection = self._map_to_frame_detection(result)
            # Load fraud labels through relationship table
            frame_detection.listFraud = self._load_fraud_labels(frame_detection.id)
            return frame_detection
        return None
    
    def find_all(self):
        """Find all result detection records"""
        query = "SELECT * FROM frame_detection"
        results = self.fetch_all(query)
        
        frame_detections = []
        for row in results:
            frame_detection = self._map_to_frame_detection(row)
            # Load fraud labels through relationship table
            frame_detection.listFraud = self._load_fraud_labels(frame_detection.id)
            frame_detections.append(frame_detection)
        
        return frame_detections
    
    def find_by_detection_id(self, detection_id):
        """Find all result detections for a specific detection"""
        query = "SELECT * FROM frame_detection WHERE detection_id = %s"
        results = self.fetch_all(query, (detection_id,))
        
        frame_detections = []
        for row in results:
            frame_detection = self._map_to_frame_detection(row)
            # Load fraud labels through relationship table
            frame_detection.listFraud = self._load_fraud_labels(frame_detection.id)
            frame_detections.append(frame_detection)
        
        return frame_detections
    
    def find_by_confidence_threshold(self, min_confidence):
        """Find result detections with confidence above threshold"""
        query = "SELECT * FROM frame_detection WHERE confidence >= %s"
        results = self.fetch_all(query, (min_confidence,))
        
        frame_detections = []
        for row in results:
            frame_detection = self._map_to_frame_detection(row)
            # Load fraud labels through relationship table
            frame_detection.listFraud = self._load_fraud_labels(frame_detection.id)
            frame_detections.append(frame_detection)
        
        return frame_detections
    
    def _map_to_frame_detection(self, row):
        """Map database row to ResultDetection object"""
        frame_detection = FrameDetection()
        frame_detection.id = row.get('id')
        frame_detection.imageUrl = row.get('image_url')
        frame_detection.bboxX = row.get('bbox_x')
        frame_detection.bboxY = row.get('bbox_y')
        frame_detection.bboxWidth = row.get('bbox_width')
        frame_detection.bboxHeight = row.get('bbox_height')
        frame_detection.confidence = row.get('confidence')
        
        # Note: detection object will be set by DetectionDAO when loading
        # to avoid circular dependency
        
        return frame_detection
    
   