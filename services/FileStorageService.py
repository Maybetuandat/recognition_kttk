import os
import shutil
from datetime import datetime
from werkzeug.utils import secure_filename
from config.config import Config


class FileStorageService:
    
    def __init__(self):
        self.base_dir = Config.BASE_DIR
        self.upload_dir = os.path.join(self.base_dir, 'uploads')
        self.video_dir = os.path.join(self.upload_dir, 'videos')
        self.flagged_frames_dir = os.path.join(self.upload_dir, 'flagged_frames')
        
        
        
        # Create directories if they don't exist
        self._create_directories()
        
        # Allowed extensions
        self.allowed_video_extensions = {'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'}
        self.allowed_image_extensions = {'jpg', 'jpeg', 'png', 'bmp', 'gif'}
    
    def _create_directories(self):
        directories = [
            self.upload_dir,
            self.video_dir,
            
            self.flagged_frames_dir,
            
            
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def is_allowed_video(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.allowed_video_extensions
    
    def save_video(self, video_file, prefix=None):
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
    
   
    
    def save_flagged_frame(self, frame, frame_number, timestamp_suffix=True):
        prefixFilename = "http://localhost:5000"
        import cv2
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
        
        return relative_path, prefixFilename + relative_path
    

  