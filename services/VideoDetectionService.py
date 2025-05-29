import cv2
import numpy as np
from datetime import datetime
import os
from services.DetectionService import DetectionService
from services.FileStorageService import FileStorageService
from services.FraudLabelService import FraudLabelService
from services.ModelService import ModelService


class VideoDetectionService:
    
    
    def __init__(self):
        self.model_service = ModelService()
        self.detection_service = DetectionService()
        self.file_storage_service = FileStorageService()
        self.fraud_label_service = FraudLabelService()
        self.detection = None
    
    def process_video(self, detection, video_path):
        model_data = self.model_service.load_model(detection.model.id)
        yolo_model = model_data['model']
        model_info = model_data['info']
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        # Create detection record
        self.detection = self.detection_service.create(detection)
        # Process video frames
        self._process_frames(
            cap, yolo_model
        )
        cap.release()
        cv2.destroyAllWindows()
        # Prepare response data
        return self.detection
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
            if frame_count % self.detection.frame_skip != 0:
                continue
            
            # Run detection
            #result se bao gom boxes: toa do cua cac bounding box,class_id, class_name, confidence
            results = yolo_model(frame, conf=self.detection.confidence_threshold)
            
            # Extract detections
            #         'class_id': int(box.cls[0]),
            #         'class_name': yolo_model.names[int(box.cls[0])],
            #         'confidence': float(box.conf[0]),
            #         'bbox': bbox
            
            current_detections = self._extract_detections(results, yolo_model)
            
            #thuc hien kiem tra voi previouse detections -> neu giong nhau thi bo qua
            if self._are_detections_similar(previous_detections, current_detections, self.detection.similarity_threshold):
                continue
            
            # loai bo cac doi tuong khong phat hien gian lan 
            frame_results = self._filter_abnormal_detections(current_detections)
            
            if not frame_results:
                continue
            
            # Save frame and detections
            self._save_frame_detections(frame, frame_results, frame_count, cap.get(cv2.CAP_PROP_FPS))    
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
            
            fraud_labels = []
            try:
                fraud_labels.append(self.fraud_label_service.get_by_class_id(det['class_id']))
            except:
                pass
            
            result = {
                'confidence': det['confidence'],
                'classId': det['class_id'],
                'className': det['class_name'],
                'listFraud': fraud_labels
            }
            
            if det['bbox']:
                x1, y1, x2, y2 = det['bbox']
                result.update({
                    'bboxX': x1,
                    'bboxY': y1,
                    'bboxWidth': x2 - x1,
                    'bboxHeight': y2 - y1
                })
            
            results.append(result)
        return results

    def _save_frame_detections(self, frame, results, frame_number, fps):
        _, image_url = self.file_storage_service.save_flagged_frame(frame, frame_number)
        
        for result in results:
            result['imageUrl'] = image_url
            try:
                newResult = self.detection_service.add_result(self.detection, result)
                self.detection.result.append(newResult)
            except Exception as e:
                print(f"Error: {e}")

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

  