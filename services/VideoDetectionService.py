import cv2
import numpy as np
from datetime import datetime
import os
from models.PhaseDetection import PhaseDetection
from models.FrameDetection import FrameDetection
from models.BoundingBoxDetection import BoundingBoxDetection
from services.FrameDetectionService import FrameDetectionService
from services.PhaseDetectionService import PhaseDetectionService
from services.FileStorageService import FileStorageService
from services.FraudLabelService import FraudLabelService
from services.ModelService import ModelService
from services.BoundingBoxDetectionService import BoundingBoxDetectionService


class VideoDetectionService:
    def __init__(self):
        self.model_service = ModelService()
        self.phase_detection_service = PhaseDetectionService()
        self.file_storage_service = FileStorageService()
        self.fraud_label_service = FraudLabelService()
        self.frame_detection_service = FrameDetectionService()
        self.bounding_box_detection_service = BoundingBoxDetectionService()
        self.phase_detection = None
    
    def process_video(self, detection, video_path):
        model_data = self.model_service.load_model(detection.model.id)
        yolo_model = model_data['model']
        model_info = model_data['info']
        
        # Open the video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        # Create detection record in database
        self.phase_detection = self.phase_detection_service.create(detection)
        
        # Process video frames
        self._process_frames(cap, yolo_model)
        
        # Clean up
        cap.release()
        cv2.destroyAllWindows()
        
        # Return the detection with results
        return self.phase_detection
    
    def _process_frames(self, cap, yolo_model):
        frame_count = 0
        previous_detections = []
        
        while True:
            # Read the next frame
            ret, frame = cap.read()
            if not ret:
                break  # End of video
            
            frame_count += 1
            
            # Skip frames according to frame_skip parameter
            if frame_count % self.phase_detection.frame_skip != 0:
                continue
            
            # Run detection on the frame
            results = yolo_model(frame, conf=self.phase_detection.confidence_threshold)
            
            # Extract detection results
            current_detections = self._extract_detections(results, yolo_model)
            
            # Skip if similar to previous frame's detections
            if self._are_detections_similar(previous_detections, current_detections, 
                                           self.phase_detection.similarity_threshold):
                continue
            
            # Filter out normal (non-fraud) detections
            bounding_boxes = self._filter_abnormal_detections(current_detections)
            
            # Skip if no fraud detections found
            if not bounding_boxes:
                continue
            
            # Save the frame and its detections
            self._save_frame_detections(frame, bounding_boxes, frame_count)
            
            # Update previous detections for next comparison
            previous_detections = current_detections
    
    def _extract_detections(self, results, yolo_model):
        detections = []
        
        if results[0].boxes is not None:
            for box in results[0].boxes:
                bbox = None
                if hasattr(box, 'xyxy'):
                    bbox = box.xyxy[0].tolist()
                
                detections.append({
                    'class_id': int(box.cls[0]),
                    'class_name': yolo_model.names[int(box.cls[0])],
                    'confidence': float(box.conf[0]),
                    'bbox': bbox
                })
                
        return detections
    
    def _filter_abnormal_detections(self, detections):
        bounding_boxes = []
        
        for det in detections:
            # Skip "normal" detections
            if det['class_name'].lower() == "normal":
                continue
            
            # Get fraud label from database
            fraud_label = None
            try:
                fraud_label = self.fraud_label_service.get_by_class_id(det['class_id'])
            except Exception as e:
                # Continue even if label not found
                pass
            
            # Create a BoundingBoxDetection object
            bbox = BoundingBoxDetection()
            bbox.fraudLabel = fraud_label
            # print(f"Fraud label for class ", bbox.fraudLabel)
            bbox.confidence = det['confidence']
            
            # Set bounding box coordinates
            if det['bbox']:
                x1, y1, x2, y2 = det['bbox']
                bbox.xCenter = x1
                bbox.yCenter = y1
                bbox.width = x2 - x1
                bbox.height = y2 - y1
            
            bounding_boxes.append(bbox)
            
        return bounding_boxes
    
    def _save_frame_detections(self, frame, bounding_boxes, frame_number):
        
        _, image_url = self.file_storage_service.save_flagged_frame(frame, frame_number)
        
        
        frame_detection = FrameDetection()
        frame_detection.imageUrl = image_url
        frame_detection.detection = self.phase_detection
        
        
        new_frame_detection = self.frame_detection_service.create(frame_detection)
        
        # Add bounding boxes to the frame detection
        for bbox in bounding_boxes:
            # Set the reference to the parent frame detection
            bbox.frameDetection = new_frame_detection
            
            # Save to database
            saved_bbox = self.bounding_box_detection_service.create(bbox)

            print(f"save boundingbox", saved_bbox.fraudLabel)
            # Add to the frame detection's list
            new_frame_detection.listBoundingBoxDetection.append(saved_bbox)
        
        # Add to the phase detection's results
        self.phase_detection.result.append(new_frame_detection)
    
    def _are_detections_similar(self, prev, curr, threshold):
        # If counts don't match or no previous detections, determine by empty status
        if len(prev) != len(curr) or not prev:
            return len(prev) == len(curr) == 0
        
        # Sort by class ID and confidence for comparison
        prev_sorted = sorted(prev, key=lambda x: (x['class_id'], -x['confidence']))
        curr_sorted = sorted(curr, key=lambda x: (x['class_id'], -x['confidence']))
        
        # Compare each detection
        for p, c in zip(prev_sorted, curr_sorted):
            # If different classes or confidence differs significantly
            if p['class_id'] != c['class_id'] or abs(p['confidence'] - c['confidence']) > (1 - threshold):
                return False
            
            # If bounding boxes differ significantly
            if p['bbox'] and c['bbox']:
                if self._calculate_iou(p['bbox'], c['bbox']) < threshold:
                    return False
                    
        return True
    
    def _calculate_iou(self, box1, box2):
        # Extract coordinates
        x1, y1, x2, y2 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        # Calculate intersection coordinates
        xi1, yi1 = max(x1, x1_2), max(y1, y1_2)
        xi2, yi2 = min(x2, x2_2), min(y2, y2_2)
        
        # No intersection
        if xi2 < xi1 or yi2 < yi1:
            return 0.0
        
        # Calculate areas
        intersection = (xi2 - xi1) * (yi2 - yi1)
        box1_area = (x2 - x1) * (y2 - y1)
        box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = box1_area + box2_area - intersection
        
        # Return IoU
        return intersection / union if union > 0 else 0.0