from dao.BaseDAO import BaseDAO
from models.BoundingBoxDetection import BoundingBoxDetection
from models.FraudLabel import FraudLabel
from models.FrameDetection import FrameDetection

class BoundingBoxDetectionDAO(BaseDAO):
    def __init__(self):
        super().__init__()
        # Table will be created when needed, not in constructor
        # to prevent circular dependencies
    
    def create_table(self):
        # Ensure frame_detection table exists first
        from dao.FrameDetectionDAO import FrameDetectionDAO
        frame_detection_dao = FrameDetectionDAO()
        frame_detection_dao.create_table()
        
        # Now create bounding_box_detection table
        query = """
        CREATE TABLE IF NOT EXISTS bounding_box_detection (
            id INT AUTO_INCREMENT PRIMARY KEY,
            fraud_label_id INT,
            frame_detection_id INT,
            x_center FLOAT,
            y_center FLOAT,
            width FLOAT,
            height FLOAT,
            confidence FLOAT,
            FOREIGN KEY (frame_detection_id) REFERENCES frame_detection(id) ON DELETE CASCADE
        )
        """
        self.execute_query(query)

    def insert(self, bbox):
        # Ensure table exists before insert
        self.create_table()
        
        query = """
        INSERT INTO bounding_box_detection 
        (fraud_label_id, frame_detection_id, x_center, y_center, width, height, confidence)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            bbox.fraudLabel.id if bbox.fraudLabel else None,
            bbox.frameDetection.id if bbox.frameDetection else None,
            bbox.xCenter,
            bbox.yCenter,
            bbox.width,
            bbox.height,
            bbox.confidence
        )
        result = self.execute_query(query, params)
        if result and isinstance(result, int):
            bbox.id = result
            return result
        return None

    def update(self, bbox):
        query = """
        UPDATE bounding_box_detection
        SET fraud_label_id = %s,
            frame_detection_id = %s,
            x_center = %s,
            y_center = %s,
            width = %s,
            height = %s,
            confidence = %s
        WHERE id = %s
        """
        params = (
            bbox.fraudLabel.id if bbox.fraudLabel else None,
            bbox.frameDetection.id if bbox.frameDetection else None,
            bbox.xCenter,
            bbox.yCenter,
            bbox.width,
            bbox.height,
            bbox.confidence,
            bbox.id
        )
        return self.execute_query(query, params)

    def delete(self, id):
        query = "DELETE FROM bounding_box_detection WHERE id = %s"
        return self.execute_query(query, (id,))

    def delete_by_frame_detection_id(self, frame_detection_id):
        """Delete all bounding boxes by frame detection ID"""
        query = "DELETE FROM bounding_box_detection WHERE frame_detection_id = %s"
        return self.execute_query(query, (frame_detection_id,))

    def find_by_id(self, id):
        query = "SELECT * FROM bounding_box_detection WHERE id = %s"
        result = self.fetch_one(query, (id,))
        if result:
            return self._map_to_bounding_box(result)
        return None

    def find_all(self):
        query = "SELECT * FROM bounding_box_detection"
        results = self.fetch_all(query)
        return [self._map_to_bounding_box(row) for row in results]

    def find_by_frame_detection_id(self, frame_detection_id):
        query = "SELECT * FROM bounding_box_detection WHERE frame_detection_id = %s"
        results = self.fetch_all(query, (frame_detection_id,))
        return [self._map_to_bounding_box(row) for row in results]

    def _map_to_bounding_box(self, row):
        bbox = BoundingBoxDetection()
        bbox.id = row.get('id')
        bbox.xCenter = row.get('x_center')
        bbox.yCenter = row.get('y_center')
        bbox.width = row.get('width')
        bbox.height = row.get('height')
        bbox.confidence = row.get('confidence')

        fraud_label_id = row.get('fraud_label_id')
        if fraud_label_id:
            # This should ideally load the complete FraudLabel from a FraudLabelDAO
            # For now, just create a placeholder with the ID
            bbox.fraudLabel = FraudLabel(id=fraud_label_id)

        frame_detection_id = row.get('frame_detection_id')
        if frame_detection_id:
            # This should ideally load the complete FrameDetection from a FrameDetectionDAO
            # For now, just create a placeholder with the ID
            bbox.frameDetection = FrameDetection(id=frame_detection_id)

        return bbox