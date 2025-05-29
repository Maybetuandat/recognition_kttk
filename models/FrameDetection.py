class FrameDetection:
    def __init__(self, id=None, detection=None, imageUrl=None, listBoundingBoxDetection=None):
        self.id = id
        self.detection = detection
        self.imageUrl = imageUrl
        self.listBoundingBoxDetection = listBoundingBoxDetection if listBoundingBoxDetection else []

    

    def to_dict(self):
        
        result_dict = {
            'id': self.id,
            'imageUrl': self.imageUrl
        }

        if self.detection:
            result_dict['detection'] = self.detection.id if hasattr(self.detection, 'id') else self.detection

        if self.listBoundingBoxDetection:
            result_dict['listBoundingBoxDetection'] = [
                bbox.to_dict() if hasattr(bbox, 'to_dict') else bbox
                for bbox in self.listBoundingBoxDetection
            ]
            
        return result_dict

    @classmethod
    def from_dict(cls, data):
        
        from .FraudLabel import FraudLabel
        
        result = cls()
        result.id = data.get('id')
        
        detection_data = data.get('detection')
        if detection_data:
            from .PhaseDetection import PhaseDetection
            if isinstance(detection_data, dict):
                result.detection = PhaseDetection.from_dict(detection_data)
            else:
                result.detection = detection_data
                
        result.imageUrl = data.get('imageUrl')
        bounding_boxes_data = data.get('listBoundingBoxDetection')
        if bounding_boxes_data:
            from .BoundingBoxDetection import BoundingBoxDetection
            result.listBoundingBoxDetection = [
                BoundingBoxDetection.from_dict(bbox) if isinstance(bbox, dict) else bbox
                for bbox in bounding_boxes_data
            ]
        else:
            result.listBoundingBoxDetection = []           
        return result
