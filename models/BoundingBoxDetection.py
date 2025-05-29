class BoundingBoxDetection:
    def __init__(self, id=None, fraudLabel=None, frameDetection=None,
                 xCenter=None, yCenter=None, width=None, height=None, confidence=None):
        self.id = id
        self.fraudLabel = fraudLabel
        self.frameDetection = frameDetection
        self.xCenter = xCenter
        self.yCenter = yCenter
        self.width = width
        self.height = height
        self.confidence = confidence

    def to_dict(self):
        result_dict = {
            'id': self.id,
            'xCenter': self.xCenter,
            'yCenter': self.yCenter,
            'width': self.width,
            'height': self.height,
            'confidence': self.confidence
        }

        if self.fraudLabel:
            result_dict['fraudLabel'] = self.fraudLabel.id if hasattr(self.fraudLabel, 'id') else self.fraudLabel

        if self.frameDetection:
            result_dict['frameDetection'] = (
                self.frameDetection.id if hasattr(self.frameDetection, 'id') else self.frameDetection
            )

        return result_dict

    @classmethod
    def from_dict(cls, data):
        from .FraudLabel import FraudLabel
        from .FrameDetection import frameDetection

        bbox = cls()
        bbox.id = data.get('id')
        bbox.xCenter = data.get('xCenter')
        bbox.yCenter = data.get('yCenter')
        bbox.width = data.get('width')
        bbox.height = data.get('height')
        bbox.confidence = data.get('confidence')

        fraud_label_data = data.get('fraudLabel')
        if fraud_label_data:
            if isinstance(fraud_label_data, dict):
                bbox.fraudLabel = FraudLabel.from_dict(fraud_label_data)
            else:
                bbox.fraudLabel = fraud_label_data

        frame_detection = data.get('frameDetection')
        if frame_detection:
            if isinstance(frame_detection, dict):
                bbox.frameDetection = frameDetection.from_dict(frame_detection)
            else:
                bbox.frameDetection = frame_detection

        return bbox
