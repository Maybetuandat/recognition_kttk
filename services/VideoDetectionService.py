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
    
    def process_video(self, detection):
        model_data = self.model_service.load_model(detection.model.id)
        yolo_model = model_data['model']
        model_info = model_data['info']

        cap = cv2.VideoCapture(detection.videoUrl)

        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {detection.videoUrl}")
        self.phase_detection = self.phase_detection_service.create(detection)
        self._process_frames(cap, yolo_model)
        
     
        cap.release()
        cv2.destroyAllWindows()
        
      
        return self.phase_detection
    
    def _process_frames(self, cap, yolo_model):
        frame_count = 0
        previous_bounding_boxes = []
        
        while True:
          
            ret, frame = cap.read()
            if not ret:
                break 
            
            frame_count += 1
            
            
            if frame_count % self.phase_detection.frame_skip != 0:
                continue
            
           #thuc hien lay result frame detect yolo model 
            results = yolo_model(frame, conf=self.phase_detection.confidence_threshold)
            
          
          # thuc hien kiem tra va lay ra cac bouding box 
            bounding_boxes, is_similar = self._process_detection_results(
                results, 
                yolo_model, 
                previous_bounding_boxes, 
                self.phase_detection.similarity_threshold
            )
            if is_similar or not bounding_boxes:
                continue
            self._save_frame_detections(frame, bounding_boxes, frame_count)
            
            previous_bounding_boxes = bounding_boxes
    
    def _process_detection_results(self, results, yolo_model, previous_bounding_boxes, similarity_threshold):
        current_raw_detections = []
        bounding_boxes = []

        #thuc hien get ra cac bounding box tu ket qua cua model va check similarity
        # doi voi mot lan detect voi mot frame, se co mot list bounding box 
        # thuc hien trich rut cac list bounding box tu ket qua cuar model 
        if results[0].boxes is not None:
            for box in results[0].boxes:
                if not hasattr(box, 'xyxy'):
                    continue
                    
                class_id = int(box.cls[0])
                class_name = yolo_model.names[class_id]
                confidence = float(box.conf[0])
                bbox = box.xyxy[0].tolist()
                
             
                if class_name.lower() == "normal":
                    continue
                
               
                current_raw_detections.append({
                    'class_id': class_id,
                    'confidence': confidence,
                    'bbox': bbox
                })
                
            
                fraud_label = None
                try:
                    fraud_label = self.fraud_label_service.get_by_class_id(class_id)
                except Exception as e:
                    pass
                
               
                bbox_obj = BoundingBoxDetection()
                bbox_obj.fraudLabel = fraud_label
                bbox_obj.confidence = confidence
                
              
                x1, y1, x2, y2 = bbox
                bbox_obj.xCenter = x1
                bbox_obj.yCenter = y1
                bbox_obj.width = x2 - x1
                bbox_obj.height = y2 - y1
                
                bounding_boxes.append(bbox_obj)
        
      
        # thuc hien kiem tra xem hai list bounding box co giong nhau hay khong
        is_similar = self._are_detections_similar(
            previous_bounding_boxes, 
            current_raw_detections, 
            bounding_boxes,
            similarity_threshold
        )
        
        return bounding_boxes, is_similar
    
    def _are_detections_similar(self, prev_bounding_boxes, curr_raw_detections, curr_bounding_boxes, threshold):

        # kiem tra xem so luong bounding box co giong nhau khong
        if len(prev_bounding_boxes) != len(curr_bounding_boxes) or not prev_bounding_boxes:
            return len(prev_bounding_boxes) == len(curr_bounding_boxes) == 0
        
       
       # thuc hien sap xep lai previouse_bounding boxes 
        prev_sorted = sorted(prev_bounding_boxes, 
                             key=lambda x: (x.fraudLabel.id if x.fraudLabel else -1, -x.confidence))
        curr_raw_sorted = sorted(curr_raw_detections, 
                              key=lambda x: (x['class_id'], -x['confidence']))
        
        

        # so sanh theo tung bounding box doi tuong, neu class id khac thi khong giong, hoac la confidence chenh lech nhau khong qua 1-threshold 
        for p, c in zip(prev_sorted, curr_raw_sorted):
            p_class_id = p.fraudLabel.id if p.fraudLabel else -1
            c_class_id = c['class_id']
            
           
            if p_class_id != c_class_id or abs(p.confidence - c['confidence']) > (1 - threshold):
                return False
            
           
           # so sanh bang tham so iou. tham so iou duoc tinh bang insertion / union
            if hasattr(p, 'xCenter') and c['bbox']:
                p_box = [p.xCenter, p.yCenter, p.xCenter + p.width, p.yCenter + p.height]
                if self._calculate_iou(p_box, c['bbox']) < threshold:
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
    
    def _save_frame_detections(self, frame, bounding_boxes, frame_number):
       
     
        _, image_url = self.file_storage_service.save_flagged_frame(frame, frame_number)
        
      
        frame_detection = FrameDetection()
        frame_detection.imageUrl = image_url
        frame_detection.detection = self.phase_detection
        
        # Save to database
        new_frame_detection = self.frame_detection_service.create(frame_detection)
        
        # Add bounding boxes to the frame detection
        for bbox in bounding_boxes:
            # Set the reference to the parent frame detection
            bbox.frameDetection = new_frame_detection
            
            # Save to database
            saved_bbox = self.bounding_box_detection_service.create(bbox)
            
            # Add to the frame detection's list
            new_frame_detection.listBoundingBoxDetection.append(saved_bbox)
        
        # Add to the phase detection's results
        self.phase_detection.result.append(new_frame_detection)