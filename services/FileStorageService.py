import os
import shutil
from datetime import datetime
from werkzeug.utils import secure_filename
from config.config import Config


class FileStorageService:
    """Service for handling file storage operations"""
    
    def __init__(self):
        self.base_dir = Config.BASE_DIR
        self.upload_dir = os.path.join(self.base_dir, 'uploads')
        self.video_dir = os.path.join(self.upload_dir, 'videos')
        self.frames_dir = os.path.join(self.upload_dir, 'frames')
        self.flagged_frames_dir = os.path.join(self.upload_dir, 'flagged_frames')
        self.visualization_dir = os.path.join(self.base_dir, 'static', 'visualizations')
        self.output_video_dir = os.path.join(self.base_dir, 'static', 'output_videos')
        
        # Create directories if they don't exist
        self._create_directories()
        
        # Allowed extensions
        self.allowed_video_extensions = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'}
        self.allowed_image_extensions = {'jpg', 'jpeg', 'png', 'bmp', 'gif'}
    
    def _create_directories(self):
        """Create all necessary directories"""
        directories = [
            self.upload_dir,
            self.video_dir,
            self.frames_dir,
            self.flagged_frames_dir,
            self.visualization_dir,
            self.output_video_dir
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def is_allowed_video(self, filename):
        """Check if video file extension is allowed"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_video_extensions
    
    def is_allowed_image(self, filename):
        """Check if image file extension is allowed"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_image_extensions
    
    def save_video(self, video_file, prefix=None):
        """
        Save uploaded video file
        
        Args:
            video_file: FileStorage object from Flask
            prefix: Optional prefix for filename
            
        Returns:
            tuple: (absolute_path, relative_path) of saved file
        """
        if not video_file or video_file.filename == '':
            raise ValueError("No video file provided")
        
        if not self.is_allowed_video(video_file.filename):
            raise ValueError(f"Invalid video file type. Allowed types: {', '.join(self.allowed_video_extensions)}")
        
        # Generate secure filename
        filename = secure_filename(video_file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if prefix:
            video_filename = f"{prefix}_{timestamp}_{filename}"
        else:
            video_filename = f"{timestamp}_{filename}"
        
        # Save file
        absolute_path = os.path.join(self.video_dir, video_filename)
        video_file.save(absolute_path)
        
        # Return both absolute and relative paths
        relative_path = f"/uploads/videos/{video_filename}"
        
        return absolute_path, relative_path
    
    def save_frame(self, frame, detection_id, frame_number, subfolder=None):
        """
        Save a single frame from video detection
        
        Args:
            frame: OpenCV frame (numpy array)
            detection_id: ID of the detection
            frame_number: Frame number in video
            subfolder: Optional subfolder name
            
        Returns:
            tuple: (absolute_path, relative_path) of saved frame
        """
        import cv2
        
        # Create detection-specific directory
        if subfolder:
            frame_dir = os.path.join(self.frames_dir, subfolder, f"detection_{detection_id}")
        else:
            frame_dir = os.path.join(self.frames_dir, f"detection_{detection_id}")
        
        os.makedirs(frame_dir, exist_ok=True)
        
        # Generate filename
        frame_filename = f"frame_{frame_number:06d}.jpg"
        absolute_path = os.path.join(frame_dir, frame_filename)
        
        # Save frame
        cv2.imwrite(absolute_path, frame)
        
        # Generate relative path
        if subfolder:
            relative_path = f"/uploads/frames/{subfolder}/detection_{detection_id}/{frame_filename}"
        else:
            relative_path = f"/uploads/frames/detection_{detection_id}/{frame_filename}"
        
        return absolute_path, relative_path
    
    def save_flagged_frame(self, frame, frame_number, timestamp_suffix=True):
        """
        Save a flagged frame (frames with abnormal detections)
        
        Args:
            frame: OpenCV frame (numpy array)
            frame_number: Frame number in video
            timestamp_suffix: Whether to add timestamp to filename
            
        Returns:
            tuple: (absolute_path, relative_path) of saved frame
        """
        import cv2
        
        # Generate filename
        if timestamp_suffix:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S%f')
            frame_filename = f"frame_{frame_number}_{timestamp}.jpg"
        else:
            frame_filename = f"frame_{frame_number:06d}.jpg"
        
        absolute_path = os.path.join(self.flagged_frames_dir, frame_filename)
        
        # Save frame
        cv2.imwrite(absolute_path, frame)
        
        # Generate relative path
        relative_path = f"/uploads/flagged_frames/{frame_filename}"
        
        return absolute_path, relative_path
    
    def save_visualization(self, image, base_name):
        """
        Save visualization image
        
        Args:
            image: OpenCV image (numpy array)
            base_name: Base name for the file
            
        Returns:
            str: Relative path of saved visualization
        """
        import cv2
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        vis_filename = f"{base_name}_vis_{timestamp}.jpg"
        vis_path = os.path.join(self.visualization_dir, vis_filename)
        
        # Save image
        cv2.imwrite(vis_path, image)
        
        return f"/static/visualizations/{vis_filename}"
    
    def save_output_video(self, video_writer, input_filename):
        """
        Generate path for output video
        
        Args:
            video_writer: Not used here, kept for compatibility
            input_filename: Original input filename
            
        Returns:
            tuple: (absolute_path, relative_path) for output video
        """
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = os.path.splitext(input_filename)[0]
        out_filename = f"{base_name}_detected_{timestamp}.mp4"
        
        absolute_path = os.path.join(self.output_video_dir, out_filename)
        relative_path = f"/static/output_videos/{out_filename}"
        
        return absolute_path, relative_path
    
    def delete_file(self, file_path):
        """
        Delete a file
        
        Args:
            file_path: Path to file (can be absolute or relative)
        """
        if not file_path:
            return
        
        # Convert relative path to absolute if needed
        if file_path.startswith('/'):
            absolute_path = os.path.join(self.base_dir, file_path.lstrip('/'))
        else:
            absolute_path = file_path
        
        if os.path.exists(absolute_path):
            os.remove(absolute_path)
    
    def delete_directory(self, dir_path):
        """
        Delete a directory and all its contents
        
        Args:
            dir_path: Path to directory
        """
        if not dir_path:
            return
        
        # Convert relative path to absolute if needed
        if dir_path.startswith('/'):
            absolute_path = os.path.join(self.base_dir, dir_path.lstrip('/'))
        else:
            absolute_path = dir_path
        
        if os.path.exists(absolute_path):
            shutil.rmtree(absolute_path)
    
    def get_file_info(self, file_path):
        """
        Get information about a file
        
        Args:
            file_path: Path to file
            
        Returns:
            dict: File information
        """
        if not os.path.exists(file_path):
            return None
        
        stat = os.stat(file_path)
        return {
            'size': stat.st_size,
            'created': datetime.fromtimestamp(stat.st_ctime),
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'extension': os.path.splitext(file_path)[1].lower()
        }
    
    def convert_to_relative_path(self, absolute_path):
        """
        Convert absolute path to relative URL path
        
        Args:
            absolute_path: Absolute file path
            
        Returns:
            str: Relative URL path
        """
        if not absolute_path:
            return None
        
        # If already a URL, return as-is
        if absolute_path.startswith('/') or absolute_path.startswith('http'):
            return absolute_path
        
        # Convert to relative path
        try:
            rel_path = os.path.relpath(absolute_path, self.base_dir)
            return '/' + rel_path.replace('\\', '/')
        except:
            return absolute_path