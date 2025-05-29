import os
from datetime import datetime, timedelta
from services.BaseService import BaseService
from services.ModelService import ModelService
from dao.DetectionDAO import DetectionDAO
from dao.ResultDetectionDAO import ResultDetectionDAO
from models.Detection import Detection
from models.ResultDetection import ResultDetection
from config.config import Config


class DetectionService(BaseService):
    def __init__(self):
        super().__init__()
        self.dao = DetectionDAO()
        self.model_service = ModelService()
        self.result_dao = ResultDetectionDAO()
    
    def create(self, detection):
        detection_id = self.dao.insert(detection)
        if detection_id:
            detection.id = detection_id
            return detection
        raise Exception("Failed to create detection")
    
    def update(self, id, data):
        """Update an existing detection record"""
        # Check if exists
        existing = self.dao.find_by_id(id)
        if not existing:
            raise ValueError(f"Detection with ID {id} not found")
        
        # Update fields
        if 'modelId' in data:
            model = self.model_service.get_by_id(data['modelId'])
            existing.model = model
        
        if 'description' in data:
            existing.description = data['description']
        
        if 'timeDetect' in data:
            existing.timeDetect = datetime.strptime(data['timeDetect'], '%Y-%m-%d %H:%M:%S')
        
        # Update in database
        if self.dao.update(existing):
            return existing
        
        raise Exception("Failed to update detection")
    
    def delete(self, id):
        """Delete a detection record"""
        # Check if exists
        existing = self.dao.find_by_id(id)
        if not existing:
            raise ValueError(f"Detection with ID {id} not found")
        
        # Delete associated images if configured
        if hasattr(Config, 'DELETE_IMAGES_ON_DETECTION_DELETE') and Config.DELETE_IMAGES_ON_DETECTION_DELETE:
            for result in existing.result:
                if result.imageUrl:
                    self._delete_image_file(result.imageUrl)
        
        # Delete (will cascade delete result detections)
        if self.dao.delete(id):
            return True
        
        raise Exception("Failed to delete detection")
    
    def get_by_id(self, id):
        """Get a detection record by ID with all results"""
        detection = self.dao.find_by_id(id)
        if not detection:
            raise ValueError(f"Detection with ID {id} not found")
        return detection
    
    def get_all(self):
        """Get all detection records"""
        return self.dao.find_all()
    
    def get_by_model(self, model_id):
        """Get all detections for a specific model"""
        # Verify model exists
        self.model_service.get_by_id(model_id)
        return self.dao.find_by_model_id(model_id)
    
    def get_by_date_range(self, start_date, end_date):
        """Get detections within a date range"""
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        
        if start_date > end_date:
            raise ValueError("Start date must be before end date")
        
        return self.dao.find_by_date_range(start_date, end_date)
    
    def add_result(self, detection, result_data):
       
        
        # Create result detection
        result = self._create_result_detection(result_data)
        result.detection = detection
        result.listFraud = result_data.lisFraud
        
        # Insert result
        result_id = self.result_dao.insert(result)
        if result_id:
            result.id = result_id
            return result
        
        raise Exception("Failed to add result to detection")
    
  
    
    def delete_result(self, result_id):
        """Delete a specific result detection"""
        # Check if exists
        existing = self.result_dao.find_by_id(result_id)
        if not existing:
            raise ValueError(f"Result detection with ID {result_id} not found")
        
        # Delete associated image if configured
        if hasattr(Config, 'DELETE_IMAGES_ON_RESULT_DELETE') and Config.DELETE_IMAGES_ON_RESULT_DELETE:
            if existing.imageUrl:
                self._delete_image_file(existing.imageUrl)
        
        # Delete
        if self.result_dao.delete(result_id):
            return True
        
        raise Exception("Failed to delete result detection")
    
    def get_statistics(self, model_id=None, start_date=None, end_date=None):
        """Get detection statistics"""
        # Get detections based on filters
        if model_id:
            detections = self.dao.find_by_model_id(model_id)
        elif start_date and end_date:
            detections = self.dao.find_by_date_range(start_date, end_date)
        else:
            detections = self.dao.find_all()
        
        # Calculate statistics
        total_detections = len(detections)
        total_results = sum(len(d.result) for d in detections)
        
        # Count by class
        class_counts = {}
        confidence_sum = 0
        confidence_count = 0
        
        for detection in detections:
            for result in detection.result:
                # Count by class
                if result.className:
                    class_counts[result.className] = class_counts.get(result.className, 0) + 1
                
                # Sum confidence
                if result.confidence:
                    confidence_sum += result.confidence
                    confidence_count += 1
        
        # Calculate average confidence
        avg_confidence = confidence_sum / confidence_count if confidence_count > 0 else 0
        
        # Find most common class
        most_common_class = max(class_counts.items(), key=lambda x: x[1])[0] if class_counts else None
        
        return {
            'total_detections': total_detections,
            'total_results': total_results,
            'average_results_per_detection': total_results / total_detections if total_detections > 0 else 0,
            'class_distribution': class_counts,
            'most_common_class': most_common_class,
            'average_confidence': avg_confidence,
            'date_range': {
                'start': min(d.timeDetect for d in detections) if detections else None,
                'end': max(d.timeDetect for d in detections) if detections else None
            }
        }
    
    def _create_result_detection(self, data):
        """Create a ResultDetection object from data"""
        result = ResultDetection(
            imageUrl=data.get('imageUrl'),
            bboxX=data.get('bboxX'),
            bboxY=data.get('bboxY'),
            bboxWidth=data.get('bboxWidth'),
            bboxHeight=data.get('bboxHeight'),
            confidence=data.get('confidence'),
            listFraud=data.get('listFraud', [])
        )
        
        # Validate bounding box
        if any([result.bboxX, result.bboxY, result.bboxWidth, result.bboxHeight]):
            if not all([result.bboxX is not None, result.bboxY is not None, 
                       result.bboxWidth is not None, result.bboxHeight is not None]):
                raise ValueError("All bounding box coordinates must be provided")
            
            if result.bboxWidth <= 0 or result.bboxHeight <= 0:
                raise ValueError("Bounding box width and height must be positive")
        
        # Validate confidence
        if result.confidence is not None:
            if result.confidence < 0 or result.confidence > 1:
                raise ValueError("Confidence must be between 0 and 1")
        
        return result
    
    def _delete_image_file(self, image_url):
        """Delete image file"""
        if not image_url:
            return
        
        filepath = os.path.join(Config.BASE_DIR, image_url.lstrip('/'))
        if os.path.exists(filepath):
            os.remove(filepath)