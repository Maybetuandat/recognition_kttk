from dao.BaseDAO import BaseDAO
from dao.ModelDAO import ModelDAO
from models.PhaseDetection import PhaseDetection
from datetime import datetime


class PhaseDetectionDAO(BaseDAO):
    def __init__(self):
        super().__init__()
        self.model_dao = ModelDAO()
        # Table will be created when needed, not in constructor
        # to prevent circular dependencies
    
    def create_table(self):
        """Create phase_detection table if not exists"""
        query = """
        CREATE TABLE IF NOT EXISTS phase_detection (
        id INT AUTO_INCREMENT PRIMARY KEY,
        model_id INT,
        time_detect DATETIME,
        description TEXT,
        confidence_threshold FLOAT,
        frame_skip INT,
        video_url VARCHAR(500),
        similarity_threshold FLOAT,
        
        FOREIGN KEY (model_id) REFERENCES model(id) ON DELETE SET NULL
        )
        """
        self.execute_query(query)
    
    def insert(self, phase_detection):
        # Ensure table exists before insert
        self.create_table()
        
        query = """
        INSERT INTO phase_detection (model_id, time_detect, description, confidence_threshold, frame_skip, video_url, similarity_threshold)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            phase_detection.model.id if phase_detection.model else None,
            phase_detection.timeDetect,
            phase_detection.description,
            phase_detection.confidence_threshold,
            phase_detection.frame_skip,
            phase_detection.videoUrl,
            phase_detection.similarity_threshold
        )

        result = self.execute_query(query, params)
        if result and isinstance(result, int):
            phase_detection.id = result
            return phase_detection
        return None
    
    def update(self, phase_detection):
        """Update an existing phase_detection record"""
        query = """
        UPDATE phase_detection
        SET model_id = %s, time_detect = %s, description = %s, confidence_threshold = %s, 
            frame_skip = %s, video_url = %s, similarity_threshold = %s
        WHERE id = %s
        """
        params = (
            phase_detection.model.id if phase_detection.model else None,
            phase_detection.timeDetect,
            phase_detection.description,
            phase_detection.confidence_threshold,
            phase_detection.frame_skip,
            phase_detection.videoUrl,
            phase_detection.similarity_threshold,
            phase_detection.id
        )
        return self.execute_query(query, params)
    
    def delete(self, id):
        """Delete a phase_detection record by id"""
        # Delete associated result phase_detections first
        from dao.FrameDetectionDAO import FrameDetectionDAO
        frame_dao = FrameDetectionDAO()
        frame_dao.delete_by_detection_id(id)
        
        # Delete phase_detection
        query = "DELETE FROM phase_detection WHERE id = %s"
        return self.execute_query(query, (id,))
    
    def find_by_id(self, id):
        """Find a phase_detection record by id with all related data"""
        query = "SELECT * FROM phase_detection WHERE id = %s"
        result = self.fetch_one(query, (id,))
        
        if result:
            phase_detection = self._map_to_phase_detection(result)
            
            # Load associated result phase_detections
            from dao.FrameDetectionDAO import FrameDetectionDAO
            frame_dao = FrameDetectionDAO()
            phase_detection.result = frame_dao.find_by_detection_id(phase_detection.id)
            
            return phase_detection
        return None
    
    def find_all(self):
        """Find all phase_detection records"""
        query = "SELECT * FROM phase_detection ORDER BY time_detect DESC"
        results = self.fetch_all(query)
        
        phase_detections = []
        for row in results:
            phase_detection = self._map_to_phase_detection(row)
            
            # Load associated result phase_detections
            from dao.FrameDetectionDAO import FrameDetectionDAO
            frame_dao = FrameDetectionDAO()
            phase_detection.result = frame_dao.find_by_detection_id(phase_detection.id)
            
            phase_detections.append(phase_detection)
        
        return phase_detections
    
   
   
    
    def _map_to_phase_detection(self, row):
        """Map database row to phase_detection object"""
        phase_detection = PhaseDetection()
        phase_detection.id = row.get('id')
        phase_detection.timeDetect = row.get('time_detect')
        phase_detection.description = row.get('description')
        phase_detection.confidence_threshold = row.get('confidence_threshold')
        phase_detection.frame_skip = row.get('frame_skip')
        phase_detection.videoUrl = row.get('video_url')
        phase_detection.similarity_threshold = row.get('similarity_threshold')
        
        # Load associated model
        model_id = row.get('model_id')
        if model_id:
            phase_detection.model = self.model_dao.find_by_id(model_id)
        
        return phase_detection