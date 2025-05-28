class ResultDetection:
    def __init__(self, id=None, detection=None, imageUrl=None, listFraud=None, 
                 bboxX=None, bboxY=None, bboxWidth=None, bboxHeight=None,
                 confidence=None, classId=None, className=None):
        self.id = id
        self.detection = detection
        self.imageUrl = imageUrl
        self.listFraud = listFraud if listFraud else []
        self.bboxX = bboxX
        self.bboxY = bboxY
        self.bboxWidth = bboxWidth
        self.bboxHeight = bboxHeight
        self.confidence = confidence
        self.classId = classId
        self.className = className

    def to_dict(self):
        
        result_dict = {
            'id': self.id,
            'imageUrl': self.imageUrl,
            'bboxX': self.bboxX,
            'bboxY': self.bboxY,
            'bboxWidth': self.bboxWidth,
            'bboxHeight': self.bboxHeight,
            'confidence': self.confidence,
            'classId': self.classId,
            'className': self.className
        }
        
        if self.detection:
            result_dict['detection'] = self.detection.id if hasattr(self.detection, 'id') else self.detection
        
        if self.listFraud:
            result_dict['listFraud'] = [
                fraud.to_dict() if hasattr(fraud, 'to_dict') else fraud
                for fraud in self.listFraud
            ]
            
        return result_dict

    @classmethod
    def from_dict(cls, data):
        
        from .FraudLabel import FraudLabel
        
        result = cls()
        result.id = data.get('id')
        
        detection_data = data.get('detection')
        if detection_data:
            from .Detection import Detection
            if isinstance(detection_data, dict):
                result.detection = Detection.from_dict(detection_data)
            else:
                result.detection = detection_data
                
        result.imageUrl = data.get('imageUrl')
        
        
        result.bboxX = data.get('bboxX')
        result.bboxY = data.get('bboxY')
        result.bboxWidth = data.get('bboxWidth')
        result.bboxHeight = data.get('bboxHeight')
        result.confidence = data.get('confidence')
        result.classId = data.get('classId')
        result.className = data.get('className')
        
        fraud_data = data.get('listFraud')
        if fraud_data:
            result.listFraud = [
                FraudLabel.from_dict(fraud) if isinstance(fraud, dict) else fraud
                for fraud in fraud_data
            ]
            
        return result
    
    def set_yolo_detection(self, box, confidence, class_id, class_name):
        if len(box) == 4:
            if isinstance(box, (list, tuple)):
                # trai tren, phai duoi
                x1, y1, x2, y2 = box
                self.bboxX = x1
                self.bboxY = y1
                self.bboxWidth = x2 - x1
                self.bboxHeight = y2 - y1
            elif hasattr(box, 'xyxy'):  # YOLOv8 box object
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                self.bboxX = x1
                self.bboxY = y1
                self.bboxWidth = x2 - x1
                self.bboxHeight = y2 - y1
            elif hasattr(box, 'xywh'):  # YOLOv8 box object
                x, y, w, h = box.xywh[0].tolist()
                self.bboxX = x
                self.bboxY = y
                self.bboxWidth = w
                self.bboxHeight = h
        
        self.confidence = confidence
        self.classId = class_id
        self.className = class_name
        return self
    
    def get_confidence_percentage(self):
        if self.confidence is not None:
            return f"{self.confidence * 100:.1f}%"
        return None
    
    def get_bounding_box_for_ui(self, image_width=None, image_height=None):
        if image_width is not None and image_height is not None:
            if 0 <= self.bboxX <= 1 and 0 <= self.bboxY <= 1 and 0 <= self.bboxWidth <= 1 and 0 <= self.bboxHeight <= 1:
                return {
                    'x': int(self.bboxX * image_width),
                    'y': int(self.bboxY * image_height),
                    'width': int(self.bboxWidth * image_width),
                    'height': int(self.bboxHeight * image_height),
                    'x1': int(self.bboxX * image_width),
                    'y1': int(self.bboxY * image_height),
                    'x2': int((self.bboxX + self.bboxWidth) * image_width),
                    'y2': int((self.bboxY + self.bboxHeight) * image_height)
                }
        return {
            'x': int(self.bboxX),
            'y': int(self.bboxY),
            'width': int(self.bboxWidth),
            'height': int(self.bboxHeight),
            'x1': int(self.bboxX),
            'y1': int(self.bboxY),
            'x2': int(self.bboxX + self.bboxWidth),
            'y2': int(self.bboxY + self.bboxHeight)
        }