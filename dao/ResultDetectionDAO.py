from dao.BaseDAO import BaseDAO
from models.ResultDetection import ResultDetection
from models.FraudLabel import FraudLabel
import json


class ResultDetectionDAO(BaseDAO):
    def __init__(self):
        super().__init__()
        self.create_table()
    
    def create_table(self):
        """Create result_detection table if not exists"""
        query = """
        CREATE TABLE IF NOT EXISTS result_detection (
            id INT AUTO_INCREMENT PRIMARY KEY,
            detection_id INT,
            image_url VARCHAR(500),
            bbox_x FLOAT,
            bbox_y FLOAT,
            bbox_width FLOAT,
            bbox_height FLOAT,
            confidence FLOAT,
            class_id INT,
            class_name VARCHAR(255),
            fraud_labels JSON,
            FOREIGN KEY (detection_id) REFERENCES detection(id) ON DELETE CASCADE
        )
        """
        self.execute_query(query)
    
    def insert(self, result_detection):
        """Insert a new result detection record"""
        # Convert fraud labels to JSON
        fraud_labels_json = None
        if result_detection.listFraud:
            fraud_labels_json = json.dumps([
                fraud.to_dict() if hasattr(fraud, 'to_dict') else fraud
                for fraud in result_detection.listFraud
            ])
        
        query = """
        INSERT INTO result_detection 
        (detection_id, image_url, bbox_x, bbox_y, bbox_width, bbox_height, 
         confidence, class_id, class_name, fraud_labels)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            result_detection.detection.id if result_detection.detection else None,
            result_detection.imageUrl,
            result_detection.bboxX,
            result_detection.bboxY,
            result_detection.bboxWidth,
            result_detection.bboxHeight,
            result_detection.confidence,
            result_detection.classId,
            result_detection.className,
            fraud_labels_json
        )
        
        result = self.execute_query(query, params)
        if result and isinstance(result, int):
            result_detection.id = result
            return result
        return None
    
    def update(self, result_detection):
        """Update an existing result detection record"""
        # Convert fraud labels to JSON
        fraud_labels_json = None
        if result_detection.listFraud:
            fraud_labels_json = json.dumps([
                fraud.to_dict() if hasattr(fraud, 'to_dict') else fraud
                for fraud in result_detection.listFraud
            ])
        
        query = """
        UPDATE result_detection
        SET detection_id = %s, image_url = %s, bbox_x = %s, bbox_y = %s, 
            bbox_width = %s, bbox_height = %s, confidence = %s, 
            class_id = %s, class_name = %s, fraud_labels = %s
        WHERE id = %s
        """
        params = (
            result_detection.detection.id if result_detection.detection else None,
            result_detection.imageUrl,
            result_detection.bboxX,
            result_detection.bboxY,
            result_detection.bboxWidth,
            result_detection.bboxHeight,
            result_detection.confidence,
            result_detection.classId,
            result_detection.className,
            fraud_labels_json,
            result_detection.id
        )
        return self.execute_query(query, params)
    
    def delete(self, id):
        """Delete a result detection record by id"""
        query = "DELETE FROM result_detection WHERE id = %s"
        return self.execute_query(query, (id,))
    
    def delete_by_detection_id(self, detection_id):
        """Delete all result detections for a specific detection"""
        query = "DELETE FROM result_detection WHERE detection_id = %s"
        return self.execute_query(query, (detection_id,))
    
    def find_by_id(self, id):
        """Find a result detection record by id"""
        query = "SELECT * FROM result_detection WHERE id = %s"
        result = self.fetch_one(query, (id,))
        
        if result:
            return self._map_to_result_detection(result)
        return None
    
    def find_all(self):
        """Find all result detection records"""
        query = "SELECT * FROM result_detection"
        results = self.fetch_all(query)
        
        return [self._map_to_result_detection(row) for row in results]
    
    def find_by_detection_id(self, detection_id):
        """Find all result detections for a specific detection"""
        query = "SELECT * FROM result_detection WHERE detection_id = %s"
        results = self.fetch_all(query, (detection_id,))
        
        return [self._map_to_result_detection(row) for row in results]
    
    def find_by_class_name(self, class_name):
        """Find result detections by class name"""
        query = "SELECT * FROM result_detection WHERE class_name = %s"
        results = self.fetch_all(query, (class_name,))
        
        return [self._map_to_result_detection(row) for row in results]
    
    def find_by_confidence_threshold(self, min_confidence):
        """Find result detections with confidence above threshold"""
        query = "SELECT * FROM result_detection WHERE confidence >= %s"
        results = self.fetch_all(query, (min_confidence,))
        
        return [self._map_to_result_detection(row) for row in results]
    
    def _map_to_result_detection(self, row):
        """Map database row to ResultDetection object"""
        result_detection = ResultDetection()
        result_detection.id = row.get('id')
        result_detection.imageUrl = row.get('image_url')
        result_detection.bboxX = row.get('bbox_x')
        result_detection.bboxY = row.get('bbox_y')
        result_detection.bboxWidth = row.get('bbox_width')
        result_detection.bboxHeight = row.get('bbox_height')
        result_detection.confidence = row.get('confidence')
        result_detection.classId = row.get('class_id')
        result_detection.className = row.get('class_name')
        
        # Parse fraud labels from JSON
        fraud_labels_json = row.get('fraud_labels')
        if fraud_labels_json:
            try:
                fraud_labels_data = json.loads(fraud_labels_json)
                result_detection.listFraud = [
                    FraudLabel.from_dict(fraud) if isinstance(fraud, dict) else fraud
                    for fraud in fraud_labels_data
                ]
            except json.JSONDecodeError:
                result_detection.listFraud = []
        
        # Note: detection object will be set by DetectionDAO when loading
        # to avoid circular dependency
        
        return result_detection