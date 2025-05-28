from dao.BaseDAO import BaseDAO
from dao.ModelDAO import ModelDAO
from models.Detection import Detection
from datetime import datetime


class DetectionDAO(BaseDAO):
    def __init__(self):
        super().__init__()
        self.model_dao = ModelDAO()
        self.create_table()
    
    def create_table(self):
        """Create detection table if not exists"""
        query = """
        CREATE TABLE IF NOT EXISTS detection (
            id INT AUTO_INCREMENT PRIMARY KEY,
            model_id INT,
            time_detect DATETIME,
            description TEXT,
            FOREIGN KEY (model_id) REFERENCES model(id) ON DELETE SET NULL
        )
        """
        self.execute_query(query)
    
    def insert(self, detection):
        """Insert a new detection record"""
        query = """
        INSERT INTO detection (model_id, time_detect, description)
        VALUES (%s, %s, %s)
        """
        params = (
            detection.model.id if detection.model else None,
            detection.timeDetect,
            detection.description
        )
        
        result = self.execute_query(query, params)
        if result and isinstance(result, int):
            detection.id = result
            
            # Insert result detections if any
            if detection.result:
                from dao.ResultDetectionDAO import ResultDetectionDAO
                result_dao = ResultDetectionDAO()
                for result_detection in detection.result:
                    result_detection.detection = detection
                    result_dao.insert(result_detection)
            
            return result
        return None
    
    def update(self, detection):
        """Update an existing detection record"""
        query = """
        UPDATE detection
        SET model_id = %s, time_detect = %s, description = %s
        WHERE id = %s
        """
        params = (
            detection.model.id if detection.model else None,
            detection.timeDetect,
            detection.description,
            detection.id
        )
        return self.execute_query(query, params)
    
    def delete(self, id):
        """Delete a detection record by id"""
        # Delete associated result detections first
        from dao.ResultDetectionDAO import ResultDetectionDAO
        result_dao = ResultDetectionDAO()
        result_dao.delete_by_detection_id(id)
        
        # Delete detection
        query = "DELETE FROM detection WHERE id = %s"
        return self.execute_query(query, (id,))
    
    def find_by_id(self, id):
        """Find a detection record by id with all related data"""
        query = "SELECT * FROM detection WHERE id = %s"
        result = self.fetch_one(query, (id,))
        
        if result:
            detection = self._map_to_detection(result)
            
            # Load associated result detections
            from dao.ResultDetectionDAO import ResultDetectionDAO
            result_dao = ResultDetectionDAO()
            detection.result = result_dao.find_by_detection_id(detection.id)
            
            return detection
        return None
    
    def find_all(self):
        """Find all detection records"""
        query = "SELECT * FROM detection ORDER BY time_detect DESC"
        results = self.fetch_all(query)
        
        detections = []
        for row in results:
            detection = self._map_to_detection(row)
            
            # Load associated result detections
            from dao.ResultDetectionDAO import ResultDetectionDAO
            result_dao = ResultDetectionDAO()
            detection.result = result_dao.find_by_detection_id(detection.id)
            
            detections.append(detection)
        
        return detections
    
    def find_by_model_id(self, model_id):
        """Find detections by model id"""
        query = "SELECT * FROM detection WHERE model_id = %s ORDER BY time_detect DESC"
        results = self.fetch_all(query, (model_id,))
        
        detections = []
        for row in results:
            detection = self._map_to_detection(row)
            
            # Load associated result detections
            from dao.ResultDetectionDAO import ResultDetectionDAO
            result_dao = ResultDetectionDAO()
            detection.result = result_dao.find_by_detection_id(detection.id)
            
            detections.append(detection)
        
        return detections
    
    def find_by_date_range(self, start_date, end_date):
        """Find detections within a date range"""
        query = """
        SELECT * FROM detection 
        WHERE time_detect BETWEEN %s AND %s 
        ORDER BY time_detect DESC
        """
        results = self.fetch_all(query, (start_date, end_date))
        
        detections = []
        for row in results:
            detection = self._map_to_detection(row)
            
            # Load associated result detections
            from dao.ResultDetectionDAO import ResultDetectionDAO
            result_dao = ResultDetectionDAO()
            detection.result = result_dao.find_by_detection_id(detection.id)
            
            detections.append(detection)
        
        return detections
    
    def _map_to_detection(self, row):
        """Map database row to Detection object"""
        detection = Detection()
        detection.id = row.get('id')
        detection.timeDetect = row.get('time_detect')
        detection.description = row.get('description')
        
        # Load associated model
        model_id = row.get('model_id')
        if model_id:
            detection.model = self.model_dao.find_by_id(model_id)
        
        return detection