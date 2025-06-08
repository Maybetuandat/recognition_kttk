import os
import shutil
from ultralytics import YOLO
from datetime import datetime
from services.BaseService import BaseService

from dao.ModelDAO import ModelDAO
from models.Model import Model
from models.TrainInfo import TrainInfo
from config.config import Config


class ModelService():
    def __init__(self):
        super().__init__()
        self.dao = ModelDAO()
        self.loaded_models = {}
        
    def get_by_id(self, id):
        model = self.dao.find_by_id(id)
        if not model:
            raise ValueError(f"Model with ID {id} not found")
        return model
    def get_all(self):
        return self.dao.find_all()
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