from datetime import datetime

from models import TrainInfo
class Model:
    def __init__(self, id = None, name = None, version = None, description = None, lastUpdate = None, trainInfo = None, modelUrl = None):
        self.id = id
        self.name = name
        self.version = version
        self.description= description
        self.lastUpdate = lastUpdate if lastUpdate else datetime.now()
        self.trainInfo = trainInfo
        self.modelUrl = modelUrl
    def to_dict(self):
        dict = {
            'id': self.id,
            'name': self.name, 
            'version': self.version, 
            'description': self.description, 
            'lastUpdate': self.lastUpdate.strftime('%Y-%m-%d %H:%M:%S') if isinstance(self.lastUpdate, datetime) else self.lastUpdate,   #chuyen thanh string 
            'modelUrl': self.modelUrl

        }
        if self.trainInfo:
            dict['trainInfo'] = self.trainInfo.to_dict() if hasattr(self.trainInfo, 'to_dict') else self.trainInfo
            dict['accuracy'] = self.trainInfo.accuracy if hasattr(self.trainInfo, 'accuracy') else None
        return dict
    @classmethod
    def from_dict(cls, data):
       
        model = cls()

        model.id = data.get('id')  
        model.name = data.get('name') 
        model.version = data.get('version')
        model.description = data.get('description')
        model.modelUrl = data.get('modelUrl')  
        last_update = data.get('lastUpdate')
        if last_update and isinstance(last_update, str):
            try:
                model.lastUpdate = datetime.strptime(
                    last_update, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                model.lastUpdate = last_update
        else:
            model.lastUpdate = last_update

        train_info_data = data.get('trainInfo')
        if train_info_data:
            if isinstance(train_info_data, dict):
                model.trainInfo = TrainInfo.from_dict(train_info_data)
            else:
                model.trainInfo = train_info_data

        return model

