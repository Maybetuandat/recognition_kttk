import cv2
import numpy as np
from datetime import datetime
import os
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
        self.phase_detection = None
        self.bounding_box_detection_service = BoundingBoxDetectionService()
    
    def process_video(self, detection, video_path):
        model_data = self.model_service.load_model(detection.model.id)
        yolo_model = model_data['model']
        model_info = model_data['info']

        
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        # Create detection record
        self.phase_detection = self.phase_detection_service.create(detection)
        # Process video frames
        self._process_frames(
            cap, yolo_model
        )
        cap.release()
        cv2.destroyAllWindows()
        # Prepare response data
        return self.phase_detection
    def _process_frames(self, cap, yolo_model):
        frame_count = 0
        previous_detections = []
     
        
        while True:
            # ret co hai gia tri: True neu doc duoc frame, False neu het video. 
            # khi doc thanh cong thi frame se la mot numpy array, co 3 chieu: height, width, channels
            ret, frame = cap.read()   
            if not ret:
                break
            
            frame_count += 1
            
            # Skip frames
            if frame_count % self.phase_detection.frame_skip != 0:
                continue
            
            # Run detection
            
            results = yolo_model(frame, conf=self.phase_detection.confidence_threshold)
            # self._export_results_to_json(results, frame_count)
            # Extract detections
            #         'class_id': int(box.cls[0]),
            #         'class_name': yolo_model.names[int(box.cls[0])],
            #         'confidence': float(box.conf[0]),
            #         'bbox': bbox
            
            current_detections = self._extract_detections(results, yolo_model)
            

            # print(f"detection ", current_detections)
            #thuc hien kiem tra voi previouse detections -> neu giong nhau thi bo qua
            if self._are_detections_similar(previous_detections, current_detections, self.phase_detection.similarity_threshold):
                continue
            
            # loai bo cac doi tuong khong phat hien gian lan 
            listBoundingBox = self._filter_abnormal_detections(current_detections)
            
            if not listBoundingBox:
                continue
            
            # Save frame and detections
            self._save_frame_detections(frame, listBoundingBox, frame_count)
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

    #loai bo cac phat hien la normal 
    def _filter_abnormal_detections(self, detections):
        results = []
        for det in detections:
            if det['class_name'].lower() == "normal":
                continue
            
            fraud_labels = None
            try:
                  fraud_labels = self.fraud_label_service.get_by_class_id(det['class_id'])
            except:
                pass
            
            result = {
                'confidence': det['confidence'],
                'fraudLabel': fraud_labels
            }
            
            if det['bbox']:
                x1, y1, x2, y2 = det['bbox']
                result.update({
                    'xCenter': x1,
                    'yCenter': y1,
                    'width': x2 - x1,
                    'height': y2 - y1
                })
            
            results.append(result)
        return results

    def _save_frame_detections(self, frame, listBoundingBox, frame_number):
        _, image_url = self.file_storage_service.save_flagged_frame(frame, frame_number)
        
        phaseDetection = None
        phaseDetection.imageUrl = image_url
        phaseDetection.detection = self.phase_detection
        phaseDetection.listBoundingBoxDetection = listBoundingBox
        newFrameDetection = self.frame_detection_service.create(phaseDetection)


        

        for bbox in listBoundingBox:
            bbox['frameDetection'] = newFrameDetection
            self.bounding_box_detection_service.create(bbox)
            newFrameDetection.listBoundingBoxDetection.append(bbox)
        
        self.phase_detection.result.append(newFrameDetection)

    def _are_detections_similar(self, prev, curr, threshold):
        if len(prev) != len(curr) or not prev:
            return len(prev) == len(curr) == 0

        prev_sorted = sorted(prev, key=lambda x: (x['class_id'], -x['confidence']))
        curr_sorted = sorted(curr, key=lambda x: (x['class_id'], -x['confidence']))
        
        for p, c in zip(prev_sorted, curr_sorted):
            if p['class_id'] != c['class_id'] or abs(p['confidence'] - c['confidence']) > (1 - threshold):
                return False
            
            if p['bbox'] and c['bbox']:
                if self._calculate_iou(p['bbox'], c['bbox']) < threshold:   # ty le giao nhau / ty le hop < threshold thi co the xem la hai bounding box khac nhau 
                    return False
        return True

    def _calculate_iou(self, box1, box2):
        x1, y1, x2, y2 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        xi1, yi1 = max(x1, x1_2), max(y1, y1_2)
        xi2, yi2 = min(x2, x2_2), min(y2, y2_2)
        
        if xi2 < xi1 or yi2 < yi1:
            return 0.0
        
        intersection = (xi2 - xi1) * (yi2 - yi1)  # tinh dien tich giao nhau
        union = (x2 - x1) * (y2 - y1) + (x2_2 - x1_2) * (y2_2 - y1_2) - intersection  # tinh dien tich hop cua 2 bounding box
        
        return intersection / union if union > 0 else 0.0   #IoU = Diện tích giao nhau / Diện tích hợp.

   