
class FraudLabel:
    def __init__(self, id=None, name=None, classId=None, color=None, createAt=None):
        self.id = id
        self.name = name
        self.classId = classId
        self.color = color
        self.createAt = createAt

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'classId': self.classId,
            'color': self.color,
            'createAt': self.createAt
        }

    @classmethod
    def from_dict(cls, data):
        fraud_label = cls()
        fraud_label.id = data.get('id')
        fraud_label.name = data.get('name')
        fraud_label.classId = data.get('classId')
        fraud_label.color = data.get('color')
        fraud_label.createAt = data.get('createAt')
        return fraud_label