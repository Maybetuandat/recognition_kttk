from datetime import datetime
from dao.ResultDetectionFraudDAO import ResultDetectionFraudDAO
from models.ResultDetectionFraud import ResultDetectionFraud


class ResultDetectionFraudService:
    """Service for managing ResultDetectionFraud objects"""
    
    def __init__(self):
        self.dao = ResultDetectionFraudDAO()
    
    def create(self, result_detection_fraud):
        """Create a new ResultDetectionFraud object in database"""
        # Validate input
        if not isinstance(result_detection_fraud, ResultDetectionFraud):
            raise ValueError("Input must be a ResultDetectionFraud object")
        
        if not result_detection_fraud.resultDetectionId:
            raise ValueError("Result detection ID is required")
        
        if not result_detection_fraud.fraudLabelId:
            raise ValueError("Fraud label ID is required")
        
        # Set created_at if not provided
        if not result_detection_fraud.createdAt:
            result_detection_fraud.createdAt = datetime.now()
        
        # Insert into database
        result_id = self.dao.insert(result_detection_fraud)
        if result_id:
            result_detection_fraud.id = result_id
            return result_detection_fraud
        
        raise Exception("Failed to create ResultDetectionFraud")
    
    def delete(self, result_detection_fraud):
        """Delete a ResultDetectionFraud object from database"""
        # Validate input
        if not isinstance(result_detection_fraud, ResultDetectionFraud):
            raise ValueError("Input must be a ResultDetectionFraud object")
        
        if result_detection_fraud.id:
            # Delete by ID
            return self.dao.delete(result_detection_fraud.id)
        elif result_detection_fraud.resultDetectionId and result_detection_fraud.fraudLabelId:
            # Delete by relationship
            return self.dao.delete_by_relationship(
                result_detection_fraud.resultDetectionId,
                result_detection_fraud.fraudLabelId
            )
        else:
            raise ValueError("Either ID or both resultDetectionId and fraudLabelId are required for deletion")
    
    def delete_by_result_detection_id(self, result_detection_id):
        """Delete all ResultDetectionFraud objects for a specific result detection"""
        if not result_detection_id:
            raise ValueError("Result detection ID is required")
        
        return self.dao.delete_by_result_detection_id(result_detection_id)