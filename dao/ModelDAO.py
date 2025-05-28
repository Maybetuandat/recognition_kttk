from dao.BaseDAO import BaseDAO
from dao.TrainInfoDAO import TrainInfoDAO
from models.Model import Model
from datetime import datetime


class ModelDAO(BaseDAO):
    def __init__(self):
        super().__init__()
        self.train_info_dao = TrainInfoDAO()
        self.create_table()
    
    def create_table(self):
        """Create model table if not exists"""
        query = """
        CREATE TABLE IF NOT EXISTS model (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            version VARCHAR(50),
            description TEXT,
            last_update DATETIME,
            train_info_id INT,
            model_url VARCHAR(500),
            FOREIGN KEY (train_info_id) REFERENCES train_info(id) ON DELETE SET NULL
        )
        """
        self.execute_query(query)
    
    def insert(self, model):
        """Insert a new model record"""
        # Insert train info first if exists
        train_info_id = None
        if model.trainInfo:
            train_info_id = self.train_info_dao.insert(model.trainInfo)
        
        query = """
        INSERT INTO model (name, version, description, last_update, train_info_id, model_url)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        params = (
            model.name,
            model.version,
            model.description,
            model.lastUpdate,
            train_info_id,
            model.modelUrl
        )
        
        result = self.execute_query(query, params)
        if result and isinstance(result, int):
            model.id = result
            return result
        return None
    
    def update(self, model):
        """Update an existing model record"""
        # Update train info if exists
        if model.trainInfo and model.trainInfo.id:
            self.train_info_dao.update(model.trainInfo)
        
        query = """
        UPDATE model
        SET name = %s, version = %s, description = %s, 
            last_update = %s, train_info_id = %s, model_url = %s
        WHERE id = %s
        """
        params = (
            model.name,
            model.version,
            model.description,
            model.lastUpdate,
            model.trainInfo.id if model.trainInfo else None,
            model.modelUrl,
            model.id
        )
        return self.execute_query(query, params)
    
    def delete(self, id):
        """Delete a model record by id"""
        # Get model to find train_info_id
        model = self.find_by_id(id)
        
        # Delete model first
        query = "DELETE FROM model WHERE id = %s"
        result = self.execute_query(query, (id,))
        
        # Delete associated train info if exists
        if result and model and model.trainInfo and model.trainInfo.id:
            self.train_info_dao.delete(model.trainInfo.id)
        
        return result
    
    def find_by_id(self, id):
        """Find a model record by id"""
        query = "SELECT * FROM model WHERE id = %s"
        result = self.fetch_one(query, (id,))
        
        if result:
            return self._map_to_model(result)
        return None
    
    def find_all(self):
        """Find all model records"""
        query = "SELECT * FROM model ORDER BY last_update DESC"
        results = self.fetch_all(query)
        
        return [self._map_to_model(row) for row in results]
    
    def find_by_name(self, name):
        """Find models by name"""
        query = "SELECT * FROM model WHERE name LIKE %s"
        results = self.fetch_all(query, (f"%{name}%",))
        
        return [self._map_to_model(row) for row in results]
    
    def find_latest_version(self, name):
        """Find the latest version of a model by name"""
        query = """
        SELECT * FROM model 
        WHERE name = %s 
        ORDER BY version DESC, last_update DESC 
        LIMIT 1
        """
        result = self.fetch_one(query, (name,))
        
        if result:
            return self._map_to_model(result)
        return None
    
    def _map_to_model(self, row):
        """Map database row to Model object"""
        model = Model()
        model.id = row.get('id')
        model.name = row.get('name')
        model.version = row.get('version')
        model.description = row.get('description')
        model.lastUpdate = row.get('last_update')
        model.modelUrl = row.get('model_url')
        
        # Load associated train info
        train_info_id = row.get('train_info_id')
        if train_info_id:
            model.trainInfo = self.train_info_dao.find_by_id(train_info_id)
        
        return model