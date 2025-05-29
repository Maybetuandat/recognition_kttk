from dao.BaseDAO import BaseDAO
from dao.ResultDetectionFraudDAO import ResultDetectionFraudDAO
from models.ResultDetection import ResultDetection
from models.ResultDetectionFraud import ResultDetectionFraud
from models.FraudLabel import FraudLabel


class ResultDetectionDAO(BaseDAO):
    def __init__(self):
        super().__init__()
        self.result_detection_fraud_dao = ResultDetectionFraudDAO()
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
            FOREIGN KEY (detection_id) REFERENCES detection(id) ON DELETE CASCADE
        )
        """
        self.execute_query(query)
    
    def insert(self, result_detection):
        """Insert a new result detection record"""
        query = """
        INSERT INTO result_detection 
        (detection_id, image_url, bbox_x, bbox_y, bbox_width, bbox_height, confidence)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            result_detection.detection.id if result_detection.detection else None,
            result_detection.imageUrl,
            result_detection.bboxX,
            result_detection.bboxY,
            result_detection.bboxWidth,
            result_detection.bboxHeight,
            result_detection.confidence
        )
        
        result = self.execute_query(query, params)
        if result and isinstance(result, int):
            result_detection.id = result
            
            # Insert fraud label relationships
            if result_detection.listFraud:
                for fraud_label in result_detection.listFraud:
                    result_detection_fraud = ResultDetectionFraud(
                        resultDetectionId=result,
                        fraudLabelId=fraud_label.id if hasattr(fraud_label, 'id') else fraud_label
                    )
                    self.result_detection_fraud_dao.insert(result_detection_fraud)
            
            return result
        return None
    
    def update(self, result_detection):
        """Update an existing result detection record"""
        query = """
        UPDATE result_detection
        SET detection_id = %s, image_url = %s, bbox_x = %s, bbox_y = %s, 
            bbox_width = %s, bbox_height = %s, confidence = %s
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
            result_detection.id
        )
        
        # Update main record
        success = self.execute_query(query, params)
        
        if success:
            # Update fraud label relationships
            # First delete all existing relationships
            self.result_detection_fraud_dao.delete_by_result_detection_id(result_detection.id)
            
            # Then insert new relationships
            if result_detection.listFraud:
                for fraud_label in result_detection.listFraud:
                    result_detection_fraud = ResultDetectionFraud(
                        resultDetectionId=result_detection.id,
                        fraudLabelId=fraud_label.id if hasattr(fraud_label, 'id') else fraud_label
                    )
                    self.result_detection_fraud_dao.insert(result_detection_fraud)
        
        return success
    
    def delete(self, id):
        """Delete a result detection record by id"""
        # Relationships will be auto-deleted due to CASCADE
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
            result_detection = self._map_to_result_detection(result)
            # Load fraud labels through relationship table
            result_detection.listFraud = self._load_fraud_labels(result_detection.id)
            return result_detection
        return None
    
    def find_all(self):
        """Find all result detection records"""
        query = "SELECT * FROM result_detection"
        results = self.fetch_all(query)
        
        result_detections = []
        for row in results:
            result_detection = self._map_to_result_detection(row)
            # Load fraud labels through relationship table
            result_detection.listFraud = self._load_fraud_labels(result_detection.id)
            result_detections.append(result_detection)
        
        return result_detections
    
    def find_by_detection_id(self, detection_id):
        """Find all result detections for a specific detection"""
        query = "SELECT * FROM result_detection WHERE detection_id = %s"
        results = self.fetch_all(query, (detection_id,))
        
        result_detections = []
        for row in results:
            result_detection = self._map_to_result_detection(row)
            # Load fraud labels through relationship table
            result_detection.listFraud = self._load_fraud_labels(result_detection.id)
            result_detections.append(result_detection)
        
        return result_detections
    
    def find_by_confidence_threshold(self, min_confidence):
        """Find result detections with confidence above threshold"""
        query = "SELECT * FROM result_detection WHERE confidence >= %s"
        results = self.fetch_all(query, (min_confidence,))
        
        result_detections = []
        for row in results:
            result_detection = self._map_to_result_detection(row)
            # Load fraud labels through relationship table
            result_detection.listFraud = self._load_fraud_labels(result_detection.id)
            result_detections.append(result_detection)
        
        return result_detections
    
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
        
        # Note: detection object will be set by DetectionDAO when loading
        # to avoid circular dependency
        
        return result_detection
    
    def _load_fraud_labels(self, result_detection_id):
        """Load fraud labels for a result detection through relationship table"""
        query = """
        SELECT fl.* FROM fraud_label fl
        INNER JOIN result_detection_fraud rdf ON fl.id = rdf.fraud_label_id
        WHERE rdf.result_detection_id = %s
        """
        results = self.fetch_all(query, (result_detection_id,))
        
        fraud_labels = []
        for row in results:
            fraud_label = FraudLabel()
            fraud_label.id = row.get('id')
            fraud_label.name = row.get('name')
            fraud_label.classId = row.get('class_id')
            fraud_label.color = row.get('color')
            fraud_label.createAt = row.get('create_at')
            fraud_labels.append(fraud_label)
        
        return fraud_labels