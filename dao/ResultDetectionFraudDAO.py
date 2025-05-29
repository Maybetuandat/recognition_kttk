from dao.BaseDAO import BaseDAO
from models.ResultDetectionFraud import ResultDetectionFraud
from datetime import datetime


class ResultDetectionFraudDAO(BaseDAO):
    def __init__(self):
        super().__init__()
        self.create_table()
    
    def create_table(self):
        """Create result_detection_fraud table if not exists"""
        query = """
        CREATE TABLE IF NOT EXISTS result_detection_fraud (
            id INT AUTO_INCREMENT PRIMARY KEY,
            result_detection_id INT NOT NULL,
            fraud_label_id INT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (result_detection_id) REFERENCES result_detection(id) ON DELETE CASCADE
        )
        """
        self.execute_query(query)
    
    def insert(self, result_detection_fraud):
        """Insert a new result detection fraud record"""
        query = """
        INSERT INTO result_detection_fraud 
        (result_detection_id, fraud_label_id, created_at)
        VALUES (%s, %s, %s)
        """
        params = (
            result_detection_fraud.resultDetectionId,
            result_detection_fraud.fraudLabelId,
            result_detection_fraud.createdAt if result_detection_fraud.createdAt else datetime.now()
        )
        
        result = self.execute_query(query, params)
        if result and isinstance(result, int):
            result_detection_fraud.id = result
            return result
        return None
    
    def delete(self, id):
        """Delete a result detection fraud record by id"""
        query = "DELETE FROM result_detection_fraud WHERE id = %s"
        return self.execute_query(query, (id,))
    
    def delete_by_result_detection_id(self, result_detection_id):
        """Delete all fraud labels for a specific result detection"""
        query = "DELETE FROM result_detection_fraud WHERE result_detection_id = %s"
        return self.execute_query(query, (result_detection_id,))
    
    def delete_by_fraud_label_id(self, fraud_label_id):
        """Delete all result detections associated with a specific fraud label"""
        query = "DELETE FROM result_detection_fraud WHERE fraud_label_id = %s"
        return self.execute_query(query, (fraud_label_id,))
    
    def delete_by_relationship(self, result_detection_id, fraud_label_id):
        """Delete a specific relationship between result detection and fraud label"""
        query = """
        DELETE FROM result_detection_fraud 
        WHERE result_detection_id = %s AND fraud_label_id = %s
        """
        return self.execute_query(query, (result_detection_id, fraud_label_id))
    
    # Required abstract methods implementation (even if not used)
    def update(self, obj):
        """Not implemented - relationship records are immutable"""
        pass
    
    def find_by_id(self, id):
        """Not implemented - use specific find methods instead"""
        pass
    
    def find_all(self):
        """Not implemented - use specific find methods instead"""
        pass