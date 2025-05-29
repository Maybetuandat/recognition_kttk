class BoundingBoxDetection:
    def __init__(self, id=None, fraudLabel=None, resultDetection=None,
                 xCenter=None, yCenter=None, width=None, height=None, confidence=None):
        self.id = id
        self.fraudLabel = fraudLabel
        self.resultDetection = resultDetection
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

        if self.resultDetection:
            result_dict['resultDetection'] = (
                self.resultDetection.id if hasattr(self.resultDetection, 'id') else self.resultDetection
            )

        return result_dict

    @classmethod
    def from_dict(cls, data):
        from .FraudLabel import FraudLabel
        from .ResultDetection import ResultDetection

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

        result_detection_data = data.get('resultDetection')
        if result_detection_data:
            if isinstance(result_detection_data, dict):
                bbox.resultDetection = ResultDetection.from_dict(result_detection_data)
            else:
                bbox.resultDetection = result_detection_data

        return bbox
