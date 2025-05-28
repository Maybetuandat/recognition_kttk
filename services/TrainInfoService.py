from services.BaseService import BaseService
from dao.TrainInfoDAO import TrainInfoDAO
from models.TrainInfo import TrainInfo
from config.config import Config


class TrainInfoService(BaseService):
    def __init__(self):
        super().__init__()
        self.dao = TrainInfoDAO()
    
    def create(self, data):
        """Create a new train info record"""
        # Validate required fields
        self.validate_data(data, required_fields=['epoch', 'learningRate', 'batchSize'])
        
        # Apply defaults if not provided
        train_info = TrainInfo(
            epoch=data.get('epoch', Config.DEFAULT_EPOCH),
            learningRate=data.get('learningRate', Config.DEFAULT_LEARNING_RATE),
            batchSize=data.get('batchSize', Config.DEFAULT_BATCH_SIZE),
            mae=data.get('mae'),
            mse=data.get('mse'),
            accuracy=data.get('accuracy'),
            timeTrain=data.get('timeTrain')
        )
        
        # Validate values
        if train_info.epoch <= 0:
            raise ValueError("Epoch must be greater than 0")
        
        if train_info.learningRate <= 0 or train_info.learningRate > 1:
            raise ValueError("Learning rate must be between 0 and 1")
        
        if train_info.batchSize <= 0:
            raise ValueError("Batch size must be greater than 0")
        
        if train_info.accuracy is not None and (train_info.accuracy < 0 or train_info.accuracy > 1):
            raise ValueError("Accuracy must be between 0 and 1")
        
        # Insert to database
        train_info_id = self.dao.insert(train_info)
        if train_info_id:
            train_info.id = train_info_id
            return train_info
        
        raise Exception("Failed to create train info")
    
    def update(self, id, data):
        """Update an existing train info record"""
        # Check if exists
        existing = self.dao.find_by_id(id)
        if not existing:
            raise ValueError(f"Train info with ID {id} not found")
        
        # Update fields
        if 'epoch' in data:
            if data['epoch'] <= 0:
                raise ValueError("Epoch must be greater than 0")
            existing.epoch = data['epoch']
        
        if 'learningRate' in data:
            if data['learningRate'] <= 0 or data['learningRate'] > 1:
                raise ValueError("Learning rate must be between 0 and 1")
            existing.learningRate = data['learningRate']
        
        if 'batchSize' in data:
            if data['batchSize'] <= 0:
                raise ValueError("Batch size must be greater than 0")
            existing.batchSize = data['batchSize']
        
        if 'mae' in data:
            existing.mae = data['mae']
        
        if 'mse' in data:
            existing.mse = data['mse']
        
        if 'accuracy' in data:
            if data['accuracy'] is not None and (data['accuracy'] < 0 or data['accuracy'] > 1):
                raise ValueError("Accuracy must be between 0 and 1")
            existing.accuracy = data['accuracy']
        
        if 'timeTrain' in data:
            existing.timeTrain = data['timeTrain']
        
        # Update in database
        if self.dao.update(existing):
            return existing
        
        raise Exception("Failed to update train info")
    
    def delete(self, id):
        """Delete a train info record"""
        # Check if exists
        existing = self.dao.find_by_id(id)
        if not existing:
            raise ValueError(f"Train info with ID {id} not found")
        
        # Check if used by any model
        from dao.ModelDAO import ModelDAO
        model_dao = ModelDAO()
        models = model_dao.find_all()
        
        for model in models:
            if model.trainInfo and model.trainInfo.id == id:
                raise ValueError(f"Cannot delete train info. It is used by model: {model.name}")
        
        # Delete
        if self.dao.delete(id):
            return True
        
        raise Exception("Failed to delete train info")
    
    def get_by_id(self, id):
        """Get a train info record by ID"""
        train_info = self.dao.find_by_id(id)
        if not train_info:
            raise ValueError(f"Train info with ID {id} not found")
        return train_info
    
    def get_all(self):
        """Get all train info records"""
        return self.dao.find_all()
    
    def calculate_metrics_summary(self, train_info_list):
        """Calculate summary statistics for a list of train info records"""
        if not train_info_list:
            return None
        
        total = len(train_info_list)
        avg_accuracy = sum(t.accuracy for t in train_info_list if t.accuracy) / total
        avg_mae = sum(t.mae for t in train_info_list if t.mae) / total
        avg_mse = sum(t.mse for t in train_info_list if t.mse) / total
        
        best_accuracy = max((t for t in train_info_list if t.accuracy), 
                          key=lambda x: x.accuracy, default=None)
        
        return {
            'total_trainings': total,
            'average_accuracy': avg_accuracy,
            'average_mae': avg_mae,
            'average_mse': avg_mse,
            'best_accuracy': best_accuracy.accuracy if best_accuracy else None,
            'best_training_id': best_accuracy.id if best_accuracy else None
        }