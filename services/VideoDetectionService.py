import cv2
import numpy as np
from datetime import datetime
from services.YOLODetectionService import YOLODetectionService
from services.DetectionService import DetectionService
from services.FileStorageService import FileStorageService
from services.FraudLabelService import FraudLabelService


class VideoDetectionService:
    """Service for smart video detection with duplicate filtering"""
    
    def __init__(self):
        self.yolo_service = YOLODetectionService()
        self.detection_service = DetectionService()
        self.file_storage_service = FileStorageService()
        self.fraud_label_service = FraudLabelService()
    
    def process_video(self, model_id, video_path, confidence_threshold=0.8, 
                     frame_skip=20, similarity_threshold=0.75):
        """
        Process video with smart detection and filtering
        
        Args:
            model_id: ID of the YOLO model to use
            video_path: Path to video file
            confidence_threshold: Minimum confidence for detections
            frame_skip: Number of frames to skip between processing
            similarity_threshold: Threshold for considering detections as similar
            
        Returns:
            dict: Processing results and statistics
        """
        # Load YOLO model
        model_data = self.yolo_service.load_model(model_id)
        yolo_model = model_data['model']
        model_info = model_data['info']
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        # Get video info
        video_info = self._get_video_info(cap, video_path)
        
        # Create detection record
        detection = self._create_detection_record(model_id, video_path, video_info)
        
        # Process video frames
        processing_stats = self._process_frames(
            cap, yolo_model, detection.id, 
            confidence_threshold, frame_skip, similarity_threshold
        )
        
        # Release resources
        cap.release()
        cv2.destroyAllWindows()
        
        # Update detection description with statistics
        self._update_detection_description(detection.id, video_path, video_info, processing_stats)
        
        # Prepare response
        return self._prepare_response(detection.id, model_info, video_info, processing_stats)
    
    def _get_video_info(self, cap, video_path):
        """Extract video information"""
        return {
            'filename': os.path.basename(video_path),
            'fps': int(cap.get(cv2.CAP_PROP_FPS)),
            'total_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        }
    
    def _create_detection_record(self, model_id, video_path, video_info):
        """Create initial detection record in database"""
        detection_data = {
            'modelId': model_id,
            'description': f"Smart video detection: {video_info['filename']} - "
                          f"{video_info['total_frames']} frames, FPS: {video_info['fps']}",
            'results': []
        }
        return self.detection_service.create(detection_data)
    
    def _process_frames(self, cap, yolo_model, detection_id, 
                       confidence_threshold, frame_skip, similarity_threshold):
        """Process video frames and return statistics"""
        stats = {
            'frame_count': 0,
            'processed_frames': 0,
            'total_detections': 0,
            'saved_detections': 0,
            'skipped_normal': 0,
            'skipped_duplicates': 0,
            'skipped_consecutive': 0
        }
        
        previous_detections = []
        recent_results = []
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            stats['frame_count'] += 1
            
            # Skip frames if requested
            if stats['frame_count'] % frame_skip != 0:
                continue
            
            stats['processed_frames'] += 1
            
            # Run detection on frame
            results = yolo_model(frame, conf=confidence_threshold)
            
            # Extract detections from frame
            current_detections = self._extract_detections(results, yolo_model)
            stats['total_detections'] += len(current_detections)
            
            # Check if similar to previous frame
            if self._are_detections_similar(previous_detections, current_detections, similarity_threshold):
                stats['skipped_duplicates'] += 1
                continue
            
            # Filter and save abnormal detections
            frame_results = self._filter_abnormal_detections(current_detections)
            
            # Skip normal detections
            stats['skipped_normal'] += len(current_detections) - len(frame_results)
            
            if not frame_results:
                continue
            
            # Check for consecutive duplicates
            if recent_results and self._are_results_same(recent_results[-1], frame_results):
                stats['skipped_consecutive'] += 1
                continue
            
            # Save frame and detections
            saved_count = self._save_frame_detections(
                frame, frame_results, detection_id, 
                stats['frame_count'], cap.get(cv2.CAP_PROP_FPS)
            )
            stats['saved_detections'] += saved_count
            
            # Update tracking lists
            recent_results.append(frame_results)
            if len(recent_results) > 10:
                recent_results.pop(0)
            
            previous_detections = current_detections
            
            # Log progress
            if stats['processed_frames'] % 100 == 0:
                self._log_progress(stats)
        
        return stats
    
    def _extract_detections(self, results, yolo_model):
        """Extract detection information from YOLO results"""
        detections = []
        
        if results[0].boxes is not None:
            boxes = results[0].boxes
            
            for box in boxes:
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                class_name = yolo_model.names[class_id]
                
                bbox = None
                if hasattr(box, 'xyxy'):
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    bbox = (x1, y1, x2, y2)
                
                detections.append({
                    'class_id': class_id,
                    'class_name': class_name,
                    'confidence': confidence,
                    'bbox': bbox
                })
        
        return detections
    
    def _filter_abnormal_detections(self, detections):
        """Filter out normal class detections and prepare results"""
        results = []
        
        for det in detections:
            # Skip "normal" class
            if det['class_name'].lower() == "normal":
                continue
            
            # Get fraud labels
            fraud_labels = []
            try:
                fraud_label = self.fraud_label_service.get_by_class_id(det['class_id'])
                fraud_labels.append(fraud_label)
            except:
                pass
            
            # Create result data
            result_data = {
                'confidence': det['confidence'],
                'classId': det['class_id'],
                'className': det['class_name'],
                'listFraud': fraud_labels
            }
            
            # Add bounding box
            if det['bbox']:
                x1, y1, x2, y2 = det['bbox']
                result_data['bboxX'] = x1
                result_data['bboxY'] = y1
                result_data['bboxWidth'] = x2 - x1
                result_data['bboxHeight'] = y2 - y1
            
            results.append(result_data)
        
        return results
    
    def _save_frame_detections(self, frame, frame_results, detection_id, frame_number, fps):
        """Save frame and add detections to database"""
        # Save flagged frame
        _, image_url = self.file_storage_service.save_flagged_frame(frame, frame_number)
        
        saved_count = 0
        for result_data in frame_results:
            result_data['imageUrl'] = image_url
            result_data['metadata'] = {
                'frame_number': frame_number,
                'timestamp': frame_number / fps,
                'video_filename': 'video'
            }
            
            try:
                self.detection_service.add_result(detection_id, result_data)
                saved_count += 1
            except Exception as e:
                print(f"Error adding result: {e}")
        
        return saved_count
    
    def _are_detections_similar(self, prev_detections, curr_detections, threshold):
        """Compare two sets of detections for similarity"""
        if len(prev_detections) != len(curr_detections):
            return False
        
        if len(prev_detections) == 0:
            return True
        
        prev_sorted = sorted(prev_detections, key=lambda x: (x['class_id'], -x['confidence']))
        curr_sorted = sorted(curr_detections, key=lambda x: (x['class_id'], -x['confidence']))
        
        for prev, curr in zip(prev_sorted, curr_sorted):
            if prev['class_id'] != curr['class_id']:
                return False
            
            conf_diff = abs(prev['confidence'] - curr['confidence'])
            if conf_diff > (1 - threshold):
                return False
            
            if prev['bbox'] and curr['bbox']:
                iou = self._calculate_iou(prev['bbox'], curr['bbox'])
                if iou < threshold:
                    return False
        
        return True
    
    def _calculate_iou(self, box1, box2):
        """Calculate Intersection over Union between two boxes"""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        if x2_i < x1_i or y2_i < y1_i:
            return 0.0
        
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def _are_results_same(self, results1, results2):
        """Check if two result sets are the same"""
        if len(results1) != len(results2):
            return False
        
        sorted1 = sorted(results1, key=lambda x: (x.get('classId', 0), x.get('confidence', 0)))
        sorted2 = sorted(results2, key=lambda x: (x.get('classId', 0), x.get('confidence', 0)))
        
        for res1, res2 in zip(sorted1, sorted2):
            if res1.get('classId') != res2.get('classId'):
                return False
            
            conf_diff = abs(res1.get('confidence', 0) - res2.get('confidence', 0))
            if conf_diff > 0.05:
                return False
            
            bbox1 = (
                res1.get('bboxX', 0), 
                res1.get('bboxY', 0),
                res1.get('bboxX', 0) + res1.get('bboxWidth', 0),
                res1.get('bboxY', 0) + res1.get('bboxHeight', 0)
            )
            
            bbox2 = (
                res2.get('bboxX', 0), 
                res2.get('bboxY', 0),
                res2.get('bboxX', 0) + res2.get('bboxWidth', 0),
                res2.get('bboxY', 0) + res2.get('bboxHeight', 0)
            )
            
            iou = self._calculate_iou(bbox1, bbox2)
            if iou < 0.9:
                return False
        
        return True
    
    def _update_detection_description(self, detection_id, video_path, video_info, stats):
        """Update detection record with final statistics"""
        import os
        
        description = (
            f"Smart video detection: {os.path.basename(video_path)} - "
            f"Processed {stats['processed_frames']}/{video_info['total_frames']} frames, "
            f"found {stats['total_detections']} objects, saved {stats['saved_detections']} abnormal objects, "
            f"skipped {stats['skipped_normal']} normal objects, "
            f"skipped {stats['skipped_duplicates']} duplicate frames, "
            f"skipped {stats['skipped_consecutive']} consecutive similar frames"
        )
        
        self.detection_service.update(detection_id, {'description': description})
    
    def _prepare_response(self, detection_id, model_info, video_info, stats):
        """Prepare response data"""
        return {
            'success': True,
            'detection_id': detection_id,
            'video_info': {
                'filename': video_info['filename'],
                'total_frames': video_info['total_frames'],
                'fps': video_info['fps'],
                'duration_seconds': video_info['total_frames'] / video_info['fps'],
                'resolution': f"{video_info['width']}x{video_info['height']}"
            },
            'processing_info': {
                'processed_frames': stats['processed_frames'],
                'frame_skip': stats.get('frame_skip', 1),
                'total_detections': stats['total_detections'],
                'saved_detections': stats['saved_detections'],
                'skipped_normal': stats['skipped_normal'],
                'skipped_duplicates': stats['skipped_duplicates'],
                'skipped_consecutive': stats['skipped_consecutive'],
                'duplicate_ratio': stats['skipped_duplicates'] / stats['processed_frames'] 
                                  if stats['processed_frames'] > 0 else 0
            },
            'model_info': {
                'id': model_info.id,
                'name': model_info.name,
                'version': model_info.version
            }
        }
    
    def _log_progress(self, stats):
        """Log processing progress"""
        print(f"Processed {stats['processed_frames']} frames, "
              f"saved {stats['saved_detections']} detections, "
              f"skipped {stats['skipped_normal']} normal objects, "
              f"skipped {stats['skipped_duplicates']} duplicates, "
              f"skipped {stats['skipped_consecutive']} consecutive similar frames")