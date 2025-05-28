from dao.base_dao import BaseDAO
from models.Model import Model
from models.TrainInfo import TrainInfo
from dao.train_info_dao import TrainInfoDAO

class ModelDAO(BaseDAO):
    def __init__(self):
        super().__init__()
        self.table = 'models'
        self.train_info_dao = TrainInfoDAO()
    
    def get_by_id(self, id):
        """Get a model by ID with its associated training information."""
        query = """
        SELECT m.*, t.id as train_info_id, t.epoch, t.learningRate, t.batchSize, 
               t.mae, t.mse, t.accuracy, t.timeTrain
        FROM models m
        LEFT JOIN train_info t ON m.id = t.model_id
        WHERE m.id = %s
        """
        
        result = self.execute_query(query, (id,))
        
        if not result:
            return None
        
        model = Model.from_dict(result)
        
        # Handle training info if present
        if result.get('train_info_id'):
            train_info_data = {
                'id': result.get('train_info_id'),
                'epoch': result.get('epoch'),
                'learningRate': result.get('learningRate'),
                'batchSize': result.get('batchSize'),
                'mae': result.get('mae'),
                'mse': result.get('mse'),
                'accuracy': result.get('accuracy'),
                'timeTrain': result.get('timeTrain')
            }
            model.trainInfo = TrainInfo.from_dict(train_info_data)
        
        return model
    
    def get_all(self):
        """Get all models with their associated training information."""
        query = """
        SELECT m.*, t.id as train_info_id, t.epoch, t.learningRate, t.batchSize, 
               t.mae, t.mse, t.accuracy, t.timeTrain
        FROM models m
        LEFT JOIN train_info t ON m.id = t.model_id
        ORDER BY m.lastUpdate DESC
        """
        
        results = self.execute_query(query, fetch=True, many=True)
        
        if not results:
            return []
        
        models = []
        for result in results:
            model = Model.from_dict(result)
            
            # Handle training info if present
            if result.get('train_info_id'):
                train_info_data = {
                    'id': result.get('train_info_id'),
                    'epoch': result.get('epoch'),
                    'learningRate': result.get('learningRate'),
                    'batchSize': result.get('batchSize'),
                    'mae': result.get('mae'),
                    'mse': result.get('mse'),
                    'accuracy': result.get('accuracy'),
                    'timeTrain': result.get('timeTrain')
                }
                model.trainInfo = TrainInfo.from_dict(train_info_data)
            
            models.append(model)
        
        return models
    
    def create(self, model):
        """Create a new model and its associated training info if present."""
        # Convert Model object to dict
        model_dict = {
            'name': model.name,
            'type': model.type,
            'version': model.version,
            'description': model.description,
            'lastUpdate': model.lastUpdate.strftime('%Y-%m-%d %H:%M:%S') if model.lastUpdate else None,
            'modelUrl': model.modelUrl
        }
        
        # Insert model
        model_id = self.execute_query(
            f"INSERT INTO {self.table} (name, type, version, description, lastUpdate, modelUrl) "
            f"VALUES (%s, %s, %s, %s, %s, %s)", 
            (model_dict['name'], model_dict['type'], model_dict['version'], 
             model_dict['description'], model_dict['lastUpdate'], model_dict['modelUrl']),
            fetch=False
        )
        
        # Set model ID
        model.id = model_id
        
        # If model has training info, create it
        if model.trainInfo:
            model.trainInfo.model_id = model_id
            self.train_info_dao.create(model.trainInfo)
        
        return model_id
    
    def update(self, model):
        """Update a model and its associated training info if present."""
        # Convert Model object to dict
        model_dict = {
            'id': model.id,
            'name': model.name,
            'type': model.type,
            'version': model.version,
            'description': model.description,
            'lastUpdate': model.lastUpdate.strftime('%Y-%m-%d %H:%M:%S') if model.lastUpdate else None,
            'modelUrl': model.modelUrl
        }
        
        # Update model
        self.execute_query(
            f"UPDATE {self.table} SET name = %s, type = %s, version = %s, description = %s, lastUpdate = %s, modelUrl = %s "
            f"WHERE id = %s",
            (model_dict['name'], model_dict['type'], model_dict['version'], model_dict['description'], 
             model_dict['lastUpdate'], model_dict['modelUrl'], model_dict['id']),
            fetch=False
        )
        
        # If model has training info, update it
        if model.trainInfo:
            if model.trainInfo.id:
                self.train_info_dao.update(model.trainInfo)
            else:
                model.trainInfo.model_id = model.id
                self.train_info_dao.create(model.trainInfo)
        
        return model.id
    
    def delete(self, id):
        """Delete a model and its associated training info."""
        # Delete associated training info first
        self.execute_query("DELETE FROM train_info WHERE model_id = %s", (id,), fetch=False)
        
        # Delete the model
        return self.execute_query(f"DELETE FROM {self.table} WHERE id = %s", (id,), fetch=False)
    
    def get_by_name(self, name):
        """Get a model by name."""
        models = self.get_all(where_clause="name = %s", params=(name,))
        return models[0] if models else None
    
    def get_by_type(self, model_type):
        """Get models by type."""
        return self.get_all(where_clause="type = %s", params=(model_type,))