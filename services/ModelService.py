import os
import shutil
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
        self.train_info_service = TrainInfoService()
    
    def create(self, data, model_file=None):
        """Create a new model record"""
        # Validate required fields
        self.validate_data(data, required_fields=['name', 'version'])
        
        # Check if model with same name and version exists
        existing_models = self.dao.find_by_name(data['name'])
        for model in existing_models:
            if model.version == data['version']:
                raise ValueError(f"Model {data['name']} version {data['version']} already exists")
        
        # Create train info if provided
        train_info = None
        if 'trainInfo' in data and data['trainInfo']:
            train_info = self.train_info_service.create(data['trainInfo'])
        
        # Handle model file upload
        model_url = None
        if model_file:
            model_url = self._save_model_file(model_file, data['name'], data['version'])
        elif 'modelUrl' in data:
            model_url = data['modelUrl']
        
        # Create model
        model = Model(
            name=data['name'],
            version=data['version'],
            description=data.get('description'),
            lastUpdate=datetime.now(),
            trainInfo=train_info,
            modelUrl=model_url
        )
        
        # Insert to database
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
        """Update an existing model record"""
        # Check if exists
        existing = self.dao.find_by_id(id)
        if not existing:
            raise ValueError(f"Model with ID {id} not found")
        
        # Check version conflict if updating version
        if 'version' in data and data['version'] != existing.version:
            models_with_version = self.dao.find_by_name(existing.name)
            for model in models_with_version:
                if model.version == data['version'] and model.id != id:
                    raise ValueError(f"Version {data['version']} already exists for model {existing.name}")
        
        # Update fields
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
        """Delete a model record"""
        # Check if exists
        existing = self.dao.find_by_id(id)
        if not existing:
            raise ValueError(f"Model with ID {id} not found")
        
        # Check if used by any detection
        from dao.DetectionDAO import DetectionDAO
        detection_dao = DetectionDAO()
        detections = detection_dao.find_by_model_id(id)
        
        if detections:
            raise ValueError(f"Cannot delete model. It is used by {len(detections)} detections")
        
        # Delete model file if exists
        if existing.modelUrl:
            self._delete_model_file(existing.modelUrl)
        
        # Delete (will also delete associated train info)
        if self.dao.delete(id):
            return True
        
        raise Exception("Failed to delete model")
    
    def get_by_id(self, id):
        """Get a model record by ID"""
        model = self.dao.find_by_id(id)
        if not model:
            raise ValueError(f"Model with ID {id} not found")
        return model
    
    def get_all(self):
        """Get all model records"""
        return self.dao.find_all()
    
    def get_by_name(self, name):
        """Get models by name"""
        return self.dao.find_by_name(name)
    
    def get_latest_version(self, name):
        """Get the latest version of a model"""
        model = self.dao.find_latest_version(name)
        if not model:
            raise ValueError(f"No model found with name {name}")
        return model
    
    def compare_versions(self, name):
        """Compare all versions of a model"""
        models = self.dao.find_by_name(name)
        if not models:
            raise ValueError(f"No models found with name {name}")
        
        # Sort by version
        models.sort(key=lambda x: x.version, reverse=True)
        
        comparisons = []
        for model in models:
            comparison = {
                'id': model.id,
                'version': model.version,
                'lastUpdate': model.lastUpdate,
                'description': model.description
            }
            
            if model.trainInfo:
                comparison['accuracy'] = model.trainInfo.accuracy
                comparison['mae'] = model.trainInfo.mae
                comparison['mse'] = model.trainInfo.mse
                comparison['trainTime'] = model.trainInfo.timeTrain
            
            comparisons.append(comparison)
        
        return comparisons
    
    def _save_model_file(self, file, model_name, version):
        """Save uploaded model file"""
        # Create model directory
        model_dir = os.path.join(Config.BASE_DIR, Config.MODEL_FOLDER)
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{model_name}_v{version}_{timestamp}.pt"
        filepath = os.path.join(model_dir, filename)
        
        # Save file
        file.save(filepath)
        
        # Return relative path
        return os.path.join(Config.MODEL_FOLDER, filename)
    
    def _delete_model_file(self, model_url):
        """Delete model file"""
        if not model_url:
            return
        
        filepath = os.path.join(Config.BASE_DIR, model_url)
        if os.path.exists(filepath):
            os.remove(filepath)