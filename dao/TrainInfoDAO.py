from .BaseDAO import BaseDAO
from models.TrainInfo import TrainInfo

class TrainInfoDAO(BaseDAO):
    def __init__(self):
        super().__init__()
        self.table = 'train_info'
    
    def get_by_id(self, id):
        """Get training information by ID."""
        result = super().get_by_id(self.table, id)
        
        if not result:
            return None
        
        return TrainInfo.from_dict(result)
    
    def get_by_model_id(self, model_id):
        """Get training information by model ID."""
        query = f"SELECT * FROM {self.table} WHERE model_id = %s"
        result = self.execute_query(query, (model_id,))
        
        if not result:
            return None
        
        return TrainInfo.from_dict(result)
    
    def get_all(self, where_clause=None, params=None, order_by=None, limit=None):
        """Get all training information records with optional filters."""
        results = super().get_all(
            self.table, 
            where_clause=where_clause, 
            params=params, 
            order_by=order_by, 
            limit=limit
        )
        
        if not results:
            return []
        
        return [TrainInfo.from_dict(result) for result in results]
    
    def create(self, train_info):
        """Create a new training information record."""
        train_info_dict = {
            'model_id': train_info.model_id,
            'epoch': train_info.epoch,
            'learningRate': train_info.learningRate,
            'batchSize': train_info.batchSize,
            'mae': train_info.mae,
            'mse': train_info.mse,
            'accuracy': train_info.accuracy,
            'timeTrain': train_info.timeTrain
        }
        
        train_info_id = super().create(self.table, train_info_dict)
        train_info.id = train_info_id
        
        return train_info_id
    
    def update(self, train_info):
        """Update a training information record."""
        train_info_dict = {
            'id': train_info.id,
            'model_id': train_info.model_id,
            'epoch': train_info.epoch,
            'learningRate': train_info.learningRate,
            'batchSize': train_info.batchSize,
            'mae': train_info.mae,
            'mse': train_info.mse,
            'accuracy': train_info.accuracy,
            'timeTrain': train_info.timeTrain
        }
        
        super().update(self.table, train_info_dict)
        
        return train_info.id
    
    def delete(self, id):
        """Delete a training information record by ID."""
        return super().delete(self.table, id)
    
    def delete_by_model_id(self, model_id):
        """Delete training information by model ID."""
        query = f"DELETE FROM {self.table} WHERE model_id = %s"
        return self.execute_query(query, (model_id,), fetch=False)