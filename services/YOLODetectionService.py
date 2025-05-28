import os
import cv2
import numpy as np
from datetime import datetime
from ultralytics import YOLO
from PIL import Image
from services.DetectionService import DetectionService
from services.ModelService import ModelService
from services.FraudLabelService import FraudLabelService
from models.Detection import Detection
from models.ResultDetection import ResultDetection
from config.config import Config


class YOLODetectionService:
    """Service for running YOLO model detection"""
    
    def __init__(self):
        self.detection_service = DetectionService()
        self.model_service = ModelService()
        self.fraud_label_service = FraudLabelService()
        self.loaded_models = {}
    
    def load_model(self, model_id):
        """Load YOLO model by model ID"""
        if model_id in self.loaded_models:
            return self.loaded_models[model_id]
        
        # Get model info from database
        model_info = self.model_service.get_by_id(model_id)
        if not model_info.modelUrl:
            raise ValueError(f"Model {model_info.name} has no model file")
        
        # Load YOLO model
        model_path = os.path.join(Config.BASE_DIR, model_info.modelUrl)
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        try:
            yolo_model = YOLO(model_path)
            self.loaded_models[model_id] = {
                'model': yolo_model,
                'info': model_info
            }
            return self.loaded_models[model_id]
        except Exception as e:
            raise Exception(f"Failed to load YOLO model: {str(e)}")
    
    def detect_single_image(self, model_id, image_path, confidence_threshold=0.5, save_visualization=True):
        """Run detection on a single image"""
        # Load model
        model_data = self.load_model(model_id)
        yolo_model = model_data['model']
        model_info = model_data['info']
        
        # Check image exists
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Run detection
        results = yolo_model(image_path, conf=confidence_threshold)
        
        # Create detection record
        detection_data = {
            'modelId': model_id,
            'description': f"Single image detection: {os.path.basename(image_path)}",
            'results': []
        }
        
        # Process results
        for r in results:
            boxes = r.boxes
            if boxes is not None:
                for box in boxes:
                    # Get detection info
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    class_name = yolo_model.names[class_id]
                    
                    # Get fraud label info
                    fraud_labels = []
                    try:
                        fraud_label = self.fraud_label_service.get_by_class_id(class_id)
                        fraud_labels.append(fraud_label)
                    except:
                        pass
                    
                    # Create result detection
                    result_data = {
                        'imageUrl': self._save_image_url(image_path),
                        'confidence': confidence,
                        'classId': class_id,
                        'className': class_name,
                        'listFraud': fraud_labels
                    }
                    
                    # Set bounding box
                    result = ResultDetection(**result_data)
                    result.set_yolo_detection(box, confidence, class_id, class_name)
                    
                    detection_data['results'].append(result.__dict__)
        
        # Save visualization if requested
        if save_visualization and detection_data['results']:
            vis_path = self._save_visualization(image_path, results[0])
            detection_data['visualizationUrl'] = vis_path
        
        # Create detection in database
        detection = self.detection_service.create(detection_data)
        
        return {
            'detection': detection,
            'total_objects': len(detection_data['results']),
            'visualization_url': detection_data.get('visualizationUrl')
        }
    
    def detect_batch_images(self, model_id, image_paths, confidence_threshold=0.5, batch_size=16):
        """Run detection on multiple images"""
        # Load model
        model_data = self.load_model(model_id)
        yolo_model = model_data['model']
        model_info = model_data['info']
        
        # Create detection record
        detection_data = {
            'modelId': model_id,
            'description': f"Batch detection on {len(image_paths)} images",
            'results': []
        }
        
        # Process images in batches
        total_objects = 0
        processed_images = 0
        
        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i:i + batch_size]
            
            # Run detection on batch
            results_list = yolo_model(batch_paths, conf=confidence_threshold)
            
            # Process each result
            for idx, (image_path, results) in enumerate(zip(batch_paths, results_list)):
                if not os.path.exists(image_path):
                    continue
                
                processed_images += 1
                boxes = results.boxes
                
                if boxes is not None:
                    for box in boxes:
                        # Get detection info
                        confidence = float(box.conf[0])
                        class_id = int(box.cls[0])
                        class_name = yolo_model.names[class_id]
                        
                        # Get fraud label info
                        fraud_labels = []
                        try:
                            fraud_label = self.fraud_label_service.get_by_class_id(class_id)
                            fraud_labels.append(fraud_label)
                        except:
                            pass
                        
                        # Create result detection
                        result_data = {
                            'imageUrl': self._save_image_url(image_path),
                            'confidence': confidence,
                            'classId': class_id,
                            'className': class_name,
                            'listFraud': fraud_labels
                        }
                        
                        # Set bounding box
                        result = ResultDetection(**result_data)
                        result.set_yolo_detection(box, confidence, class_id, class_name)
                        
                        detection_data['results'].append(result.__dict__)
                        total_objects += 1
        
        # Create detection in database
        detection = self.detection_service.create(detection_data)
        
        return {
            'detection': detection,
            'processed_images': processed_images,
            'total_objects': total_objects,
            'average_objects_per_image': total_objects / processed_images if processed_images > 0 else 0
        }
    
    def detect_video(self, model_id, video_path, confidence_threshold=0.5, frame_skip=1, save_output=True):
        """Run detection on video"""
        # Load model
        model_data = self.load_model(model_id)
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
        
        # Create output video writer if requested
        out_writer = None
        output_path = None
        if save_output:
            output_path = self._get_output_video_path(video_path)
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out_writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Create detection record
        detection_data = {
            'modelId': model_id,
            'description': f"Video detection: {os.path.basename(video_path)} ({total_frames} frames)",
            'results': []
        }
        
        # Process video
        frame_count = 0
        processed_frames = 0
        total_detections = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Skip frames if requested
            if frame_count % frame_skip != 0:
                continue
            
            processed_frames += 1
            
            # Run detection
            results = yolo_model(frame, conf=confidence_threshold)
            
            # Draw results on frame
            annotated_frame = results[0].plot()
            
            # Save annotated frame
            if out_writer:
                out_writer.write(annotated_frame)
            
            # Process detections
            boxes = results[0].boxes
            if boxes is not None:
                total_detections += len(boxes)
        
        # Release resources
        cap.release()
        if out_writer:
            out_writer.release()
        cv2.destroyAllWindows()
        
        # Save detection summary
        detection_data['description'] += f" - Processed {processed_frames} frames, found {total_detections} objects"
        if output_path:
            detection_data['videoOutputUrl'] = output_path
        
        # Create detection in database
        detection = self.detection_service.create(detection_data)
        
        return {
            'detection': detection,
            'total_frames': total_frames,
            'processed_frames': processed_frames,
            'total_detections': total_detections,
            'output_video': output_path
        }
    
    def get_model_classes(self, model_id):
        """Get list of classes that the model can detect"""
        model_data = self.load_model(model_id)
        yolo_model = model_data['model']
        
        classes = []
        for class_id, class_name in yolo_model.names.items():
            # Try to get fraud label info
            fraud_label = None
            try:
                fraud_label = self.fraud_label_service.get_by_class_id(class_id)
            except:
                pass
            
            classes.append({
                'classId': class_id,
                'className': class_name,
                'fraudLabel': fraud_label.to_dict() if fraud_label else None
            })
        
        return classes
    
    def _save_image_url(self, image_path):
        """Convert absolute path to relative URL"""
        # If already a URL, return as-is
        if image_path.startswith('/') or image_path.startswith('http'):
            return image_path
        
        # Convert to relative path
        rel_path = os.path.relpath(image_path, Config.BASE_DIR)
        return '/' + rel_path.replace('\\', '/')
    
    def _save_visualization(self, image_path, results):
        """Save visualization of detection results"""
        # Create visualization directory
        vis_dir = os.path.join(Config.BASE_DIR, 'static', 'visualizations')
        os.makedirs(vis_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        vis_filename = f"{base_name}_vis_{timestamp}.jpg"
        vis_path = os.path.join(vis_dir, vis_filename)
        
        # Save annotated image
        annotated = results.plot()
        cv2.imwrite(vis_path, annotated)
        
        return f"/static/visualizations/{vis_filename}"
    
    def _get_output_video_path(self, input_path):
        """Generate output video path"""
        # Create output directory
        out_dir = os.path.join(Config.BASE_DIR, 'static', 'output_videos')
        os.makedirs(out_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        out_filename = f"{base_name}_detected_{timestamp}.mp4"
        
        return os.path.join(out_dir, out_filename)