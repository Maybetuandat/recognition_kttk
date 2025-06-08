from dao.BaseDAO import BaseDAO
from models.FrameDetection import FrameDetection
from models.PhaseDetection import PhaseDetection


class FrameDetectionDAO(BaseDAO):
    def __init__(self):
        super().__init__()
        # Table will be created when needed, not in constructor
        # to prevent circular dependencies
    
    def create_table(self):
        # Ensure phase_detection table exists first
        from dao.PhaseDetectionDAO import PhaseDetectionDAO
        phase_detection_dao = PhaseDetectionDAO()
        phase_detection_dao.create_table()
        
        # Now create frame_detection table
        query = """
        CREATE TABLE IF NOT EXISTS frame_detection (
            id INT AUTO_INCREMENT PRIMARY KEY,
            detection_id INT,
            image_url VARCHAR(500),
            FOREIGN KEY (detection_id) REFERENCES phase_detection(id) ON DELETE CASCADE
        )
        """
        self.execute_query(query)
    
    def insert(self, frame_detection):
        # Ensure table exists before insert
        self.create_table()
        
        query = """
        INSERT INTO frame_detection 
        (detection_id, image_url)
        VALUES (%s, %s)
        """
        params = (
            frame_detection.detection.id if frame_detection.detection else None,
            frame_detection.imageUrl
        )
        
        id = self.execute_query(query, params)
        if id and isinstance(id, int):
            frame_detection.id = id
            
            
            
            return frame_detection
        return None
    
    def update(self, frame_detection):
        """Update an existing frame detection record"""
        # Ensure table exists before update
        self.create_table()
        
        query = """
        UPDATE frame_detection
        SET detection_id = %s, image_url = %s
        WHERE id = %s
        """
        params = (
            frame_detection.detection.id if frame_detection.detection else None,
            frame_detection.imageUrl,
            frame_detection.id
        )
        
        # Update main record
        success = self.execute_query(query, params)
        
        # Update bounding boxes
        if success and frame_detection.listBoundingBoxDetection:
            from dao.BoundingBoxDetectionDAO import BoundingBoxDetectionDAO
            bbox_dao = BoundingBoxDetectionDAO()
            # Delete existing bounding boxes
            bbox_dao.delete_by_frame_detection_id(frame_detection.id)
            
            # Insert new bounding boxes
            for bbox in frame_detection.listBoundingBoxDetection:
                bbox.frameDetection = frame_detection
                bbox_dao.insert(bbox)
        
        return success
    
    def delete(self, id):
        """Delete a frame detection record by id"""
        # Relationships will be auto-deleted due to CASCADE
        query = "DELETE FROM frame_detection WHERE id = %s"
        return self.execute_query(query, (id,))
    
    def delete_by_detection_id(self, detection_id):
        """Delete all frame detections for a specific detection"""
        query = "DELETE FROM frame_detection WHERE detection_id = %s"
        return self.execute_query(query, (detection_id,))
    
    def find_by_id(self, id):
        """Find a frame detection record by id"""
        # Ensure table exists before query
        self.create_table()
        
        query = "SELECT * FROM frame_detection WHERE id = %s"
        result = self.fetch_one(query, (id,))
        
        if result:
            frame_detection = self._map_to_frame_detection(result)
            # Load bounding boxes
            from dao.BoundingBoxDetectionDAO import BoundingBoxDetectionDAO
            bbox_dao = BoundingBoxDetectionDAO()
            frame_detection.listBoundingBoxDetection = bbox_dao.find_by_frame_detection_id(frame_detection.id)
            return frame_detection
        return None
    
    def find_all(self):
        """Find all frame detection records"""
        # Ensure table exists before query
        self.create_table()
        
        query = "SELECT * FROM frame_detection"
        results = self.fetch_all(query)
        
        frame_detections = []
        for row in results:
            frame_detection = self._map_to_frame_detection(row)
            # Load bounding boxes
            from dao.BoundingBoxDetectionDAO import BoundingBoxDetectionDAO
            bbox_dao = BoundingBoxDetectionDAO()
            frame_detection.listBoundingBoxDetection = bbox_dao.find_by_frame_detection_id(frame_detection.id)
            frame_detections.append(frame_detection)
        
        return frame_detections
    
    def find_by_detection_id(self, detection_id):
        """Find all frame detections for a specific detection"""
        # Ensure table exists before query
        self.create_table()
        
        query = "SELECT * FROM frame_detection WHERE detection_id = %s"
        results = self.fetch_all(query, (detection_id,))
        
        frame_detections = []
        for row in results:
            frame_detection = self._map_to_frame_detection(row)
            # Load bounding boxes
            from dao.BoundingBoxDetectionDAO import BoundingBoxDetectionDAO
            bbox_dao = BoundingBoxDetectionDAO()
            frame_detection.listBoundingBoxDetection = bbox_dao.find_by_frame_detection_id(frame_detection.id)
            frame_detections.append(frame_detection)
        
        return frame_detections
    
    def _map_to_frame_detection(self, row):
        """Map database row to FrameDetection object"""
        frame_detection = FrameDetection()
        frame_detection.id = row.get('id')
        frame_detection.imageUrl = row.get('image_url')
        
        # Note: detection object will be set by PhaseDetectionDAO when loading
        # to avoid circular dependency
        detection_id = row.get('detection_id')
        if detection_id:
            frame_detection.detection = PhaseDetection(id=detection_id)
        
        return frame_detection