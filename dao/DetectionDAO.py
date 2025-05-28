from dao.BaseDAO import BaseDAO
from models.Detection import Detection
from models.Model import Model
from models.ResultDetection import ResultDetection
from dao.ModelDAO import ModelDAO
from dao.ResultDetectionDAO import ResultDetectionDAO

class DetectionDAO(BaseDAO):
    def __init__(self):
        super().__init__()
        self.table = 'detections'
        self.model_dao = ModelDAO()
        self.result_detection_dao = ResultDetectionDAO()
    
    def get_by_id(self, id):
        """Get a detection by ID with its associated model and results."""
        query = """
        SELECT d.*, m.id as model_id, m.name as model_name, m.type as model_type, 
               m.version as model_version, m.description as model_description, 
               m.lastUpdate as model_lastUpdate, m.modelUrl as model_modelUrl
        FROM detections d
        LEFT JOIN models m ON d.model_id = m.id
        WHERE d.id = %s
        """
        
        result = self.execute_query(query, (id,))
        
        if not result:
            return None
        
        detection = Detection()
        detection.id = result['id']
        detection.timeDetect = result['timeDetect']
        detection.description = result['description']
        
        # Handle model if present
        if result.get('model_id'):
            model_data = {
                'id': result.get('model_id'),
                'name': result.get('model_name'),
                'type': result.get('model_type'),
                'version': result.get('model_version'),
                'description': result.get('model_description'),
                'lastUpdate': result.get('model_lastUpdate'),
                'modelUrl': result.get('model_modelUrl')
            }
            detection.model = Model.from_dict(model_data)
        
        # Get detection results
        detection_results = self.result_detection_dao.get_by_detection_id(id)
        if detection_results:
            detection.result = detection_results
        
        return detection
    
    def get_all(self, where_clause=None, params=None, order_by="timeDetect DESC", limit=None):
        """Get all detections with their associated models."""
        query = """
        SELECT d.*, m.id as model_id, m.name as model_name, m.type as model_type, 
               m.version as model_version, m.description as model_description, 
               m.lastUpdate as model_lastUpdate, m.modelUrl as model_modelUrl
        FROM detections d
        LEFT JOIN models m ON d.model_id = m.id
        """
        
        if where_clause:
            query += f" WHERE {where_clause}"
        
        if order_by:
            query += f" ORDER BY {order_by}"
        
        if limit:
            query += f" LIMIT {limit}"
        
        results = self.execute_query(query, params, fetch=True, many=True)
        
        if not results:
            return []
        
        detections = []
        for result in results:
            detection = Detection()
            detection.id = result['id']
            detection.timeDetect = result['timeDetect']
            detection.description = result['description']
            
            # Handle model if present
            if result.get('model_id'):
                model_data = {
                    'id': result.get('model_id'),
                    'name': result.get('model_name'),
                    'type': result.get('model_type'),
                    'version': result.get('model_version'),
                    'description': result.get('model_description'),
                    'lastUpdate': result.get('model_lastUpdate'),
                    'modelUrl': result.get('model_modelUrl')
                }
                detection.model = Model.from_dict(model_data)
            
            detections.append(detection)
        
        # For efficiency, we don't load results here - they can be loaded on demand
        
        return detections
    
    def create(self, detection):
        """Create a new detection and its associated results."""
        # Convert Detection object to dict
        detection_dict = {
            'model_id': detection.model.id if detection.model else None,
            'timeDetect': detection.timeDetect.strftime('%Y-%m-%d %H:%M:%S') if detection.timeDetect else None,
            'description': detection.description
        }
        
        # Insert detection
        detection_id = super().create(self.table, detection_dict)
        
        # Set detection ID
        detection.id = detection_id
        
        # If detection has results, create them
        if detection.result:
            for result in detection.result:
                result.detection = detection_id
                self.result_detection_dao.create(result)
        
        return detection_id
    
    def update(self, detection):
        """Update a detection and its associated results."""
        # Convert Detection object to dict
        detection_dict = {
            'id': detection.id,
            'model_id': detection.model.id if detection.model else None,
            'timeDetect': detection.timeDetect.strftime('%Y-%m-%d %H:%M:%S') if detection.timeDetect else None,
            'description': detection.description
        }
        
        # Update detection
        super().update(self.table, detection_dict)
        
        # For results, we assume they are managed separately (through ResultDetectionDAO)
        
        return detection.id
    
    def delete(self, id):
        """Delete a detection and its associated results."""
        # Delete associated results first
        self.result_detection_dao.delete_by_detection_id(id)
        
        # Delete the detection
        return super().delete(self.table, id)
    
    def get_by_model_id(self, model_id):
        """Get detections by model ID."""
        return self.get_all(where_clause="model_id = %s", params=(model_id,))
    
    def count_by_model_id(self, model_id):
        """Count detections by model ID."""
        query = f"SELECT COUNT(*) as count FROM {self.table} WHERE model_id = %s"
        result = self.execute_query(query, (model_id,))
        return result['count'] if result else 0