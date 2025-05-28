import os
import cv2
import numpy as np
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime

from services.DetectionService import DetectionService
from services.ModelService import ModelService
from config.config import Config


class VideoDetectionController:
    def __init__(self):
        self.detection_service = DetectionService()
        self.model_service = ModelService()
        self.allowed_extensions = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'}
        self.upload_dir = os.path.join(Config.BASE_DIR, 'uploads', 'videos')
        os.makedirs(self.upload_dir, exist_ok=True)
        self.flagged_frames_dir = os.path.join(Config.BASE_DIR, 'uploads', 'flagged_frames')
        os.makedirs(self.flagged_frames_dir, exist_ok=True)
        self.similarity_threshold = 0.95
    
    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def detect_video(self):
        try:
            if 'model_id' not in request.form:
                return jsonify({'error': 'model_id is required'}), 400
            if 'video' not in request.files:
                return jsonify({'error': 'video file is required'}), 400
            
            # Get parameters
            model_id = int(request.form.get('model_id'))
            # nguong co phep du doan dung 
            confidence_threshold = float(request.form.get('confidence_threshold', 0.8))

            # so luong frame skip 
            frame_skip = int(request.form.get('frame_skip', 20))

            # su dung de loai bo cac doi tuong bi lap
            similarity_threshold = float(request.form.get('similarity_threshold', 0.75))
            
            
            try:
                model = self.model_service.get_by_id(model_id)
            except Exception as e:
                return jsonify({'error': f'Invalid model_id: {str(e)}'}), 404
            
            # Get video file
            video_file = request.files['video']
            if video_file.filename == '':
                return jsonify({'error': 'No video file selected'}), 400
            
            if not self.allowed_file(video_file.filename):
                return jsonify({'error': f'Invalid file type. Allowed types: {", ".join(self.allowed_extensions)}'}), 400
            
            # luu video vao backend 
            filename = secure_filename(video_file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            video_filename = f"{timestamp}_{filename}"
            video_path = os.path.join(self.upload_dir, video_filename)
            video_file.save(video_path)
            
            # Process video
            result = self._process_video(
                model_id=model_id,
                video_path=video_path,
                confidence_threshold=confidence_threshold,
                frame_skip=frame_skip,
                similarity_threshold=similarity_threshold
            )
            
            return jsonify(result), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def _process_video(self, model_id, video_path, confidence_threshold, frame_skip, similarity_threshold):
       
        
        # Load YOLO model
        model_data = self.model_service.load_model(model_id)
        yolo_model = model_data['model']
        model_info = model_data['info']
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
        
        # Get video info
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Create detection record
        detection_data = {
            'modelId': model_id,
            'description': f"Smart video detection: {os.path.basename(video_path)} - {total_frames} frames, FPS: {fps}",
            'results': []
        }
        
        # Create initial detection in database
        detection = self.detection_service.create(detection_data)
        
        # Process video
        frame_count = 0
        processed_frames = 0
        total_detections = 0
        saved_detections = 0
        skipped_normal = 0
        skipped_duplicates = 0
        skipped_consecutive = 0
        
        # Store previous detections for frame-to-frame comparison
        previous_detections = []
        
        # Store list of recent results to avoid consecutive duplicates
        recent_results = []
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # Skip frames if requested
                if frame_count % frame_skip != 0:
                    continue
                
                processed_frames += 1
                
                # Run detection on frame
                results = yolo_model(frame, conf=confidence_threshold)
                
                # Extract current frame detections
                current_detections = []
                
                frame_has_abnormal_detection = False
                
                if results[0].boxes is not None:
                    boxes = results[0].boxes
                    
                    for box in boxes:
                        # Get detection info
                        confidence = float(box.conf[0])
                        class_id = int(box.cls[0])
                        class_name = yolo_model.names[class_id]
                        
                        # Get bounding box
                        if hasattr(box, 'xyxy'):
                            x1, y1, x2, y2 = box.xyxy[0].tolist()
                            bbox = (x1, y1, x2, y2)
                        else:
                            bbox = None
                        
                        # Check if this is not a "normal" class
                        if class_name.lower() != "normal":
                            frame_has_abnormal_detection = True
                        
                        current_detections.append({
                            'class_id': class_id,
                            'class_name': class_name,
                            'confidence': confidence,
                            'bbox': bbox
                        })
                        
                        total_detections += 1
                
                # Check if current detections are similar to previous frame
                if self._are_detections_similar(previous_detections, current_detections, similarity_threshold):
                    skipped_duplicates += 1
                    continue
                
                # Filter and prepare frame results
                frame_results = []
                
                # Process detections in this frame
                for det in current_detections:
                    # Skip "normal" class detections
                    if det['class_name'].lower() == "normal":
                        skipped_normal += 1
                        continue
                    
                    # Get fraud labels
                    fraud_labels = []
                    try:
                        fraud_label = self.yolo_service.fraud_label_service.get_by_class_id(det['class_id'])
                        fraud_labels.append(fraud_label)
                    except:
                        pass
                    
                    # Create result detection data
                    result_data = {
                        'confidence': det['confidence'],
                        'classId': det['class_id'],
                        'className': det['class_name'],
                        'listFraud': fraud_labels,
                        'metadata': {
                            'frame_number': frame_count,
                            'timestamp': frame_count / fps,
                            'video_filename': os.path.basename(video_path)
                        }
                    }
                    
                    # Set bounding box
                    if det['bbox']:
                        x1, y1, x2, y2 = det['bbox']
                        result_data['bboxX'] = x1
                        result_data['bboxY'] = y1
                        result_data['bboxWidth'] = x2 - x1
                        result_data['bboxHeight'] = y2 - y1
                    
                    frame_results.append(result_data)
                
                # Skip if there are no results after filtering out "normal" detections
                if not frame_results:
                    continue
                
                # Check if the current results match the most recent saved results
                should_save = True
                if recent_results:
                    # Compare current results with the most recent saved results
                    # This compares consecutive frames with similar detections
                    if self._are_results_same(recent_results[-1], frame_results):
                        skipped_consecutive += 1
                        should_save = False
                
                if should_save:
                    # Save the frame image
                    frame_filename = f"frame_{frame_count}_{datetime.now().strftime('%Y%m%d_%H%M%S%f')}.jpg"
                    frame_path = os.path.join(self.flagged_frames_dir, frame_filename)
                    cv2.imwrite(frame_path, frame)
                    
                    # Create relative URL path for the image
                    image_url = f"/uploads/flagged_frames/{frame_filename}"
                    
                    # Add image URL to each result
                    for result_data in frame_results:
                        result_data['imageUrl'] = image_url
                        
                        # Add result to detection
                        try:
                            result = self.detection_service.add_result(detection.id, result_data)
                            saved_detections += 1
                        except Exception as e:
                            print(f"Error adding result: {e}")
                    
                    # Add to recent results list
                    recent_results.append(frame_results)
                    # Keep only the most recent results
                    if len(recent_results) > 10:
                        recent_results.pop(0)
                
                # Update previous detections for frame-to-frame comparison
                previous_detections = current_detections
                
                # Log progress
                if processed_frames % 100 == 0:
                    print(f"Processed {processed_frames}/{total_frames} frames, "
                          f"saved {saved_detections} detections, skipped {skipped_normal} normal objects, "
                          f"skipped {skipped_duplicates} duplicates, skipped {skipped_consecutive} consecutive similar frames")
        
        finally:
            # Release resources
            cap.release()
            cv2.destroyAllWindows()
        
        # Update detection description with final statistics
        update_data = {
            'description': f"Smart video detection: {os.path.basename(video_path)} - "
                          f"Processed {processed_frames}/{total_frames} frames, "
                          f"found {total_detections} objects, saved {saved_detections} abnormal objects, "
                          f"skipped {skipped_normal} normal objects, skipped {skipped_duplicates} duplicate frames, "
                          f"skipped {skipped_consecutive} consecutive similar frames"
        }
        self.detection_service.update(detection.id, update_data)
        
        # Prepare response
        response = {
            'success': True,
            'detection_id': detection.id,
            'video_info': {
                'filename': os.path.basename(video_path),
                'total_frames': total_frames,
                'fps': fps,
                'duration_seconds': total_frames / fps,
                'resolution': f"{width}x{height}"
            },
            'processing_info': {
                'processed_frames': processed_frames,
                'frame_skip': frame_skip,
                'total_detections': total_detections,
                'saved_detections': saved_detections,
                'skipped_normal': skipped_normal,
                'skipped_duplicates': skipped_duplicates,
                'skipped_consecutive': skipped_consecutive,
                'duplicate_ratio': skipped_duplicates / processed_frames if processed_frames > 0 else 0
            },
            'model_info': {
                'id': model_info.id,
                'name': model_info.name,
                'version': model_info.version
            }
        }
        
        return response
    
    def _are_detections_similar(self, prev_detections, curr_detections, threshold):
        """
        Compare two sets of detections to check if they are similar
        Returns True if detections are similar (should skip), False otherwise
        """
        # If different number of detections, they're not similar
        if len(prev_detections) != len(curr_detections):
            return False
        
        # If both empty, they're similar
        if len(prev_detections) == 0:
            return True
        
        # Sort detections by class_id and confidence for consistent comparison
        prev_sorted = sorted(prev_detections, key=lambda x: (x['class_id'], -x['confidence']))
        curr_sorted = sorted(curr_detections, key=lambda x: (x['class_id'], -x['confidence']))
        
        # Compare each detection
        for prev, curr in zip(prev_sorted, curr_sorted):
            # Check class match
            if prev['class_id'] != curr['class_id']:
                return False
            
            # Check confidence similarity
            conf_diff = abs(prev['confidence'] - curr['confidence'])
            if conf_diff > (1 - threshold):
                return False
            
            # Check bounding box similarity (IoU)
            if prev['bbox'] and curr['bbox']:
                iou = self._calculate_iou(prev['bbox'], curr['bbox'])
                if iou < threshold:
                    return False
        
        return True
    
    def _calculate_iou(self, box1, box2):
        """Calculate Intersection over Union (IoU) between two boxes"""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        # Calculate intersection
        x1_i = max(x1_1, x1_2)
        y1_i = max(y1_1, y1_2)
        x2_i = min(x2_1, x2_2)
        y2_i = min(y2_1, y2_2)
        
        if x2_i < x1_i or y2_i < y1_i:
            return 0.0
        
        intersection = (x2_i - x1_i) * (y2_i - y1_i)
        
        # Calculate union
        area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
        area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0.0
    
    def _are_results_same(self, results1, results2):
        """
        Compare two sets of detection results to check if they are the same.
        This is used to avoid saving consecutive frames with identical results.
        
        Args:
            results1: List of result data from the first frame
            results2: List of result data from the second frame
            
        Returns:
            bool: True if results are the same, False otherwise
        """
        # If different number of detections, they're not the same
        if len(results1) != len(results2):
            return False
        
        # Compare detections based on class and bounding box
        # Sort by classId for consistent comparison
        sorted1 = sorted(results1, key=lambda x: (x.get('classId', 0), x.get('confidence', 0)))
        sorted2 = sorted(results2, key=lambda x: (x.get('classId', 0), x.get('confidence', 0)))
        
        for res1, res2 in zip(sorted1, sorted2):
            # Check if class matches
            if res1.get('classId') != res2.get('classId'):
                return False
                
            # Check if confidence is close enough
            conf_diff = abs(res1.get('confidence', 0) - res2.get('confidence', 0))
            if conf_diff > 0.05:  # 5% confidence difference threshold
                return False
                
            # Check if bounding boxes are similar
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
            
            # Calculate IoU between bounding boxes
            iou = self._calculate_iou(bbox1, bbox2)
            if iou < 0.9:  # 90% IoU threshold
                return False
                
        return True
        """Get summary of detection results grouped by time intervals"""
        try:
            # Get detection
            detection = self.detection_service.get_by_id(detection_id)
            
            # Group results by time intervals (e.g., every 5 seconds)
            interval_seconds = 5
            time_groups = {}
            
            for result in detection.result:
                # Extract timestamp from metadata if available
                timestamp = 0
                if hasattr(result, 'metadata') and result.metadata:
                    timestamp = result.metadata.get('timestamp', 0)
                
                # Calculate time interval
                interval = int(timestamp // interval_seconds)
                
                if interval not in time_groups:
                    time_groups[interval] = {
                        'start_time': interval * interval_seconds,
                        'end_time': (interval + 1) * interval_seconds,
                        'detections': [],
                        'class_summary': {}
                    }
                
                # Add detection to interval
                time_groups[interval]['detections'].append({
                    'id': result.id,
                    'className': result.className,
                    'confidence': result.confidence,
                    'timestamp': timestamp,
                    'imageUrl': result.imageUrl
                })
                
                # Update class summary
                class_name = result.className
                if class_name not in time_groups[interval]['class_summary']:
                    time_groups[interval]['class_summary'][class_name] = 0
                time_groups[interval]['class_summary'][class_name] += 1
            
            # Convert to sorted list
            summary = []
            for interval in sorted(time_groups.keys()):
                group = time_groups[interval]
                summary.append({
                    'time_range': f"{group['start_time']:.1f}s - {group['end_time']:.1f}s",
                    'detection_count': len(group['detections']),
                    'class_distribution': group['class_summary'],
                    'average_confidence': sum(d['confidence'] for d in group['detections']) / len(group['detections']) if group['detections'] else 0,
                    'sample_images': [d['imageUrl'] for d in group['detections'][:3]]  # Include sample images
                })
            
            return jsonify({
                'success': True,
                'detection_id': detection_id,
                'total_detections': len(detection.result),
                'time_summary': summary
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def register_routes(self, app):
        """Register routes with Flask app"""
        app.add_url_rule('/api/detection/video', 'detect_video', self.detect_video, methods=['POST'])
      