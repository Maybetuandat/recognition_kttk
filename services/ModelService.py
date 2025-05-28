import os
import shutil
from ultralytics import YOLO
from datetime import datetime
from services.BaseService import BaseService
from services.TrainInfoService import TrainInfoService
from dao.ModelDAO import ModelDAO
from models.Model import Model
from models.TrainInfo import TrainInfo
from config.config import Config


class ModelService(BaseService):
    def __init__(self):
        super().__init__()
        self.dao = ModelDAO()
        self.loaded_models = {}
        self.train_info_service = TrainInfoService()
    
    def create(self, data, model_file=None):
        #check xem trong form gui den co cac thuoc tinh nay khong 
        self.validate_data(data, required_fields=['name', 'version'])
        
        
        existing_models = self.dao.find_by_name(data['name'])
        for model in existing_models:
            if model.version == data['version']:
                raise ValueError(f"Model {data['name']} version {data['version']} already exists")
        
        
        train_info = None
        if 'trainInfo' in data and data['trainInfo']:
            train_info = self.train_info_service.create(data['trainInfo'])
        
        
        model_url = None
        if model_file:
            model_url = self._save_model_file(model_file, data['name'], data['version'])
        elif 'modelUrl' in data:
            model_url = data['modelUrl']
        
        
        model = Model(
            name=data['name'],
            version=data['version'],
            description=data.get('description'),
            lastUpdate=datetime.now(),
            trainInfo=train_info,
            modelUrl=model_url
        )
        
        
        model_id = self.dao.insert(model)
        if model_id:
            model.id = model_id
            return model
        
        # Rollback if failed
        if train_info:
            self.train_info_service.delete(train_info.id)
        if model_url and model_file:
            self._delete_model_file(model_url)
        
        raise Exception("Failed to create model")
    
    def update(self, id, data, model_file=None):
        
        
        existing = self.dao.find_by_id(id)
        if not existing:
            raise ValueError(f"Model with ID {id} not found")
        
        # Check version conflict if updating version
        if 'version' in data and data['version'] != existing.version:
            models_with_version = self.dao.find_by_name(existing.name)
            for model in models_with_version:
                if model.version == data['version'] and model.id != id:
                    raise ValueError(f"Version {data['version']} already exists for model {existing.name}")
        
        
        if 'name' in data:
            existing.name = data['name']
        
        if 'version' in data:
            existing.version = data['version']
        
        if 'description' in data:
            existing.description = data['description']
        
        # Update model file if provided
        if model_file:
            # Delete old file if exists
            if existing.modelUrl:
                self._delete_model_file(existing.modelUrl)
            # Save new file
            existing.modelUrl = self._save_model_file(model_file, existing.name, existing.version)
        
        # Update train info if provided
        if 'trainInfo' in data and data['trainInfo']:
            if existing.trainInfo:
                self.train_info_service.update(existing.trainInfo.id, data['trainInfo'])
            else:
                train_info = self.train_info_service.create(data['trainInfo'])
                existing.trainInfo = train_info
        
        existing.lastUpdate = datetime.now()
        
        # Update in database
        if self.dao.update(existing):
            return existing
        
        raise Exception("Failed to update model")
    
    def delete(self, id):
        existing = self.dao.find_by_id(id)
        if not existing:
            raise ValueError(f"Model with ID {id} not found")
        from dao.DetectionDAO import DetectionDAO
        detection_dao = DetectionDAO()
        detections = detection_dao.find_by_model_id(id)
        if detections:
            raise ValueError(f"Cannot delete model. It is used by {len(detections)} detections")
        if existing.modelUrl:
            self._delete_model_file(existing.modelUrl)
        if self.dao.delete(id):
            return True
        raise Exception("Failed to delete model")
    
    def get_by_id(self, id):
        model = self.dao.find_by_id(id)
        if not model:
            raise ValueError(f"Model with ID {id} not found")
        return model
    def get_all(self):
        return self.dao.find_all()
    def _save_model_file(self, file, model_name, version):
        # tao directory neu chua co 
        model_dir = os.path.join(Config.BASE_DIR, Config.MODEL_FOLDER)
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
        
        #tao ten 
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{model_name}_v{version}_{timestamp}.pt"
        filepath = os.path.join(model_dir, filename)
        
        
        file.save(filepath)
        
        
        return os.path.join(Config.MODEL_FOLDER, filename)
    def _delete_model_file(self, model_url):
        
        if not model_url:
            return
        
        filepath = os.path.join(Config.BASE_DIR, model_url)
        if os.path.exists(filepath):
            os.remove(filepath)
    def load_model(self, model_id):
        
        if model_id in self.loaded_models:
            return self.loaded_models[model_id]
        model_info = self.get_by_id(model_id)
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