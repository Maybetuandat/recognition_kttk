from datetime import datetime


class PhaseDetection:
    def __init__(self, id=None, model=None, timeDetect=None, videoUrl = None, description=None,  result=None, confidence_threshold = None, frame_skip = None, similarity_threshold = None):
        self.id = id  
        self.model = model
        self.timeDetect = timeDetect if timeDetect else datetime.now()
        self.description = description
        self.confidence_threshold = confidence_threshold
        self.frame_skip = frame_skip
        self.videoUrl = videoUrl if videoUrl else None
        self.similarity_threshold = similarity_threshold
        self.result = result if result else []

    def to_dict(self):
        
        detection_dict = {
            'id': self.id,  
            'timeDetect': self.timeDetect.strftime('%Y-%m-%d %H:%M:%S') if isinstance(self.timeDetect, datetime) else self.timeDetect,
            'description': self.description,
            'similarity_threshold': self.similarity_threshold, 
            'frame_skip': self.frame_skip,
            'confidence_threshold': self.confidence_threshold,
            'videoUrl': self.videoUrl
            
        }
        
        if self.model:
            detection_dict['model'] = self.model.to_dict() if hasattr(self.model, 'to_dict') else self.model
            
        if self.result:
            detection_dict['result'] = [
                res.to_dict() if hasattr(res, 'to_dict') else res
                for res in self.result
            ]
        return detection_dict

    @classmethod
    def from_dict(cls, data):
        
        from .Model import Model
        from .FrameDetection import FrameDetection  
        
        detection = cls()
        detection.id = data.get('id')  
        detection.description = data.get('description')
        detection.confidence_threshold = data.get('confidence_threshold')
        detection.similarity_threshold = data.get('similarity_threshold')
        detection.frame_skip = data.get('frame_skip')
        detection.videoUrl = data.get('videoUrl')
        
        time_detect = data.get('timeDetect')
        if time_detect and isinstance(time_detect, str):   #kiem tra xem time_detect la string
            try:
                detection.timeDetect = datetime.strptime(
                    time_detect, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                detection.timeDetect = time_detect
        else:
            detection.timeDetect = time_detect
        model = data.get('model')
        if model:
            detection.model = Model.from_dict(
                model) if isinstance(model, dict) else model
        result = data.get('result')
        if result:
            detection.result = [
                FrameDetection.from_dict(res) if isinstance(
                    res, dict) else res
                for res in result
            ]

        return detection