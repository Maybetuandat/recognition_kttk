import os
import cv2
import tempfile
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime
from services.YOLODetectionService import YOLODetectionService
from services.DetectionService import DetectionService
from services.ModelService import ModelService
from config.config import Config


class VideoDetectionController:
    def __init__(self):
        self.yolo_service = YOLODetectionService()
        self.detection_service = DetectionService()
        self.model_service = ModelService()
        
        # Allowed video extensions
        self.allowed_extensions = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'}
        
        # Create upload directory
        self.upload_dir = os.path.join(Config.BASE_DIR, 'uploads', 'videos')
        os.makedirs(self.upload_dir, exist_ok=True)
        
        # Create frames directory
        self.frames_dir = os.path.join(Config.BASE_DIR, 'uploads', 'frames')
        os.makedirs(self.frames_dir, exist_ok=True)
    
    def allowed_file(self, filename):
        """Check if file extension is allowed"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def detect_video(self):
        """
        Handle video detection request
        Expected request data:
        - model_id: ID of the model to use
        - video: Video file
        - confidence_threshold: Optional confidence threshold (default: 0.5)
        - frame_skip: Optional frame skip interval (default: 1)
        - save_frames: Optional flag to save detected frames (default: True)
        """
        try:
            # Validate request
            if 'model_id' not in request.form:
                return jsonify({'error': 'model_id is required'}), 400
            
            if 'video' not in request.files:
                return jsonify({'error': 'video file is required'}), 400
            
            # Get parameters
            model_id = int(request.form.get('model_id'))
            confidence_threshold = float(request.form.get('confidence_threshold', 0.5))
            frame_skip = int(request.form.get('frame_skip', 1))
            save_frames = request.form.get('save_frames', 'true').lower() == 'true'
            
            # Validate model exists
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
            
            # Save video temporarily
            filename = secure_filename(video_file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            video_filename = f"{timestamp}_{filename}"
            video_path = os.path.join(self.upload_dir, video_filename)
            video_file.save(video_path)
            
            # Process video and extract frames
            result = self._process_video_with_frames(
                model_id=model_id,
                video_path=video_path,
                confidence_threshold=confidence_threshold,
                frame_skip=frame_skip,
                save_frames=save_frames
            )
            
            return jsonify(result), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def _process_video_with_frames(self, model_id, video_path, confidence_threshold, frame_skip, save_frames):
        """Process video, extract frames, and save detections to database"""
        
        # Load YOLO model
        model_data = self.yolo_service.load_model(model_id)
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
            'description': f"Video detection: {os.path.basename(video_path)} - {total_frames} frames, FPS: {fps}",
            'results': []
        }
        
        # Create initial detection in database
        detection = self.detection_service.create(detection_data)
        
        # Process video frame by frame
        frame_count = 0
        processed_frames = 0
        total_detections = 0
        frames_with_detections = 0
        
        # Create directory for this detection's frames
        detection_frames_dir = os.path.join(self.frames_dir, f"detection_{detection.id}")
        os.makedirs(detection_frames_dir, exist_ok=True)
        
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
                
                # Process detections in this frame
                frame_has_detections = False
                if results[0].boxes is not None:
                    boxes = results[0].boxes
                    
                    if len(boxes) > 0:
                        frame_has_detections = True
                        frames_with_detections += 1
                        
                        # Save frame if requested
                        frame_filename = None
                        if save_frames:
                            frame_filename = f"frame_{frame_count:06d}.jpg"
                            frame_path = os.path.join(detection_frames_dir, frame_filename)
                            cv2.imwrite(frame_path, frame)
                        
                        # Process each detection in the frame
                        for box in boxes:
                            # Get detection info
                            confidence = float(box.conf[0])
                            class_id = int(box.cls[0])
                            class_name = yolo_model.names[class_id]
                            
                            # Get fraud labels
                            fraud_labels = []
                            try:
                                fraud_label = self.yolo_service.fraud_label_service.get_by_class_id(class_id)
                                fraud_labels.append(fraud_label)
                            except:
                                pass
                            
                            # Create result detection data
                            result_data = {
                                'imageUrl': f"/uploads/frames/detection_{detection.id}/{frame_filename}" if frame_filename else None,
                                'confidence': confidence,
                                'classId': class_id,
                                'className': class_name,
                                'listFraud': fraud_labels
                            }
                            
                            # Get bounding box coordinates
                            if hasattr(box, 'xyxy'):
                                x1, y1, x2, y2 = box.xyxy[0].tolist()
                                result_data['bboxX'] = x1
                                result_data['bboxY'] = y1
                                result_data['bboxWidth'] = x2 - x1
                                result_data['bboxHeight'] = y2 - y1
                            
                            # Add metadata
                            result_data['metadata'] = {
                                'frame_number': frame_count,
                                'timestamp': frame_count / fps,  # Time in seconds
                                'video_filename': os.path.basename(video_path)
                            }
                            
                            # Add result to detection
                            try:
                                result = self.detection_service.add_result(detection.id, result_data)
                                total_detections += 1
                            except Exception as e:
                                print(f"Error adding result: {e}")
                
                # Log progress every 100 frames
                if processed_frames % 100 == 0:
                    print(f"Processed {processed_frames}/{total_frames} frames, found {total_detections} objects")
        
        finally:
            # Release resources
            cap.release()
            cv2.destroyAllWindows()
        
        # Update detection description with final statistics
        update_data = {
            'description': f"Video detection: {os.path.basename(video_path)} - Processed {processed_frames}/{total_frames} frames, " + 
                          f"found {total_detections} objects in {frames_with_detections} frames"
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
                'frames_with_detections': frames_with_detections,
                'total_detections': total_detections,
                'average_detections_per_frame': total_detections / processed_frames if processed_frames > 0 else 0
            },
            'model_info': {
                'id': model_info.id,
                'name': model_info.name,
                'version': model_info.version
            },
            'frames_saved': save_frames,
            'frames_directory': f"/uploads/frames/detection_{detection.id}" if save_frames else None
        }
        
        return response
    
    def get_detection_frames(self, detection_id):
        """Get all frames for a specific detection"""
        try:
            # Verify detection exists
            detection = self.detection_service.get_by_id(detection_id)
            
            # Get all results for this detection
            results = detection.result
            
            # Group results by frame
            frames = {}
            for result in results:
                if result.imageUrl:
                    # Extract frame number from image URL
                    frame_num = self._extract_frame_number(result.imageUrl)
                    if frame_num not in frames:
                        frames[frame_num] = {
                            'frame_number': frame_num,
                            'image_url': result.imageUrl,
                            'detections': []
                        }
                    
                    frames[frame_num]['detections'].append({
                        'id': result.id,
                        'className': result.className,
                        'confidence': result.confidence,
                        'bbox': {
                            'x': result.bboxX,
                            'y': result.bboxY,
                            'width': result.bboxWidth,
                            'height': result.bboxHeight
                        },
                        'fraudLabels': [label.to_dict() for label in result.listFraud] if result.listFraud else []
                    })
            
            # Convert to sorted list
            sorted_frames = sorted(frames.values(), key=lambda x: x['frame_number'])
            
            return jsonify({
                'success': True,
                'detection_id': detection_id,
                'total_frames': len(sorted_frames),
                'frames': sorted_frames
            }), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def _extract_frame_number(self, image_url):
        """Extract frame number from image URL"""
        try:
            # Extract filename from URL
            filename = os.path.basename(image_url)
            # Extract frame number (assuming format: frame_XXXXXX.jpg)
            if filename.startswith('frame_'):
                frame_str = filename.replace('frame_', '').replace('.jpg', '')
                return int(frame_str)
        except:
            pass
        return 0
    
    def register_routes(self, app):
        """Register routes with Flask app"""
        app.add_url_rule('/api/detection/video', 'detect_video', self.detect_video, methods=['POST'])
        app.add_url_rule('/api/detection/<int:detection_id>/frames', 'get_detection_frames', 
                        self.get_detection_frames, methods=['GET'])