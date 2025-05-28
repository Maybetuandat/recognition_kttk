from dao.BaseDAO import BaseDAO
from models.ResultDetection import ResultDetection

class ResultDetectionDAO(BaseDAO):
    def __init__(self):
        super().__init__()
        self.table = 'result_detections'
    
    def get_by_id(self, id):
        """Get a result detection by ID."""
        query = f"SELECT * FROM {self.table} WHERE id = %s"
        result = self.execute_query(query, (id,))
        
        if not result:
            return None
        
        return ResultDetection.from_dict(result)
    
    def get_by_detection_id(self, detection_id):
        """Get result detections by detection ID."""
        query = f"SELECT * FROM {self.table} WHERE detection = %s"
        results = self.execute_query(query, (detection_id,), fetch=True, many=True)
        
        if not results:
            return []
        
        return [ResultDetection.from_dict(result) for result in results]
    
    def create(self, result_detection):
        """Create a new result detection."""
        # Convert ResultDetection object to dict
        result_dict = {
            'detection': result_detection.detection,
            'imageUrl': result_detection.imageUrl,
            'bboxX': result_detection.bboxX,
            'bboxY': result_detection.bboxY,
            'bboxWidth': result_detection.bboxWidth,
            'bboxHeight': result_detection.bboxHeight,
            'confidence': result_detection.confidence,
            'classId': result_detection.classId,
            'className': result_detection.className
        }
        
        # Insert result detection
        result_id = super().create(self.table, result_dict)
        
        # Set result detection ID
        result_detection.id = result_id
        
        # Note: Since FraudLabels are from an external service, we don't need to store them
        # The listFraud property will still be available in the ResultDetection object
        # but won't be persisted to the database
        
        return result_id
    
    def update(self, result_detection):
        """Update a result detection."""
        # Convert ResultDetection object to dict
        result_dict = {
            'id': result_detection.id,
            'detection': result_detection.detection,
            'imageUrl': result_detection.imageUrl,
            'bboxX': result_detection.bboxX,
            'bboxY': result_detection.bboxY,
            'bboxWidth': result_detection.bboxWidth,
            'bboxHeight': result_detection.bboxHeight,
            'confidence': result_detection.confidence,
            'classId': result_detection.classId,
            'className': result_detection.className
        }
        
        # Update result detection
        super().update(self.table, result_dict)
        
        return result_detection.id
    
    def delete(self, id):
        """Delete a result detection."""
        return super().delete(self.table, id)
    
    def delete_by_detection_id(self, detection_id):
        """Delete result detections by detection ID."""
        query = f"DELETE FROM {self.table} WHERE detection = %s"
        return self.execute_query(query, (detection_id,), fetch=False)