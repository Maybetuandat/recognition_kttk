from dao.BaseDAO import BaseDAO
from models.TrainInfo import TrainInfo


class TrainInfoDAO(BaseDAO):
    def __init__(self):
        super().__init__()
        self.create_table()
    
    def create_table(self):
        """Create train_info table if not exists"""
        query = """
        CREATE TABLE IF NOT EXISTS train_info (
            id INT AUTO_INCREMENT PRIMARY KEY,
            epoch INT,
            learning_rate FLOAT,
            batch_size INT,
            mae FLOAT,
            mse FLOAT,
            accuracy FLOAT,
            time_train VARCHAR(255)
        )
        """
        self.execute_query(query)
    
    def insert(self, train_info):
        """Insert a new train info record"""
        query = """
        INSERT INTO train_info (epoch, learning_rate, batch_size, mae, mse, accuracy, time_train)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            train_info.epoch,
            train_info.learningRate,
            train_info.batchSize,
            train_info.mae,
            train_info.mse,
            train_info.accuracy,
            train_info.timeTrain
        )
        
        result = self.execute_query(query, params)
        if result and isinstance(result, int):
            train_info.id = result
            return result
        return None
    
    def update(self, train_info):
        """Update an existing train info record"""
        query = """
        UPDATE train_info
        SET epoch = %s, learning_rate = %s, batch_size = %s, 
            mae = %s, mse = %s, accuracy = %s, time_train = %s
        WHERE id = %s
        """
        params = (
            train_info.epoch,
            train_info.learningRate,
            train_info.batchSize,
            train_info.mae,
            train_info.mse,
            train_info.accuracy,
            train_info.timeTrain,
            train_info.id
        )
        return self.execute_query(query, params)
    
    def delete(self, id):
        """Delete a train info record by id"""
        query = "DELETE FROM train_info WHERE id = %s"
        return self.execute_query(query, (id,))
    
    def find_by_id(self, id):
        """Find a train info record by id"""
        query = "SELECT * FROM train_info WHERE id = %s"
        result = self.fetch_one(query, (id,))
        
        if result:
            return self._map_to_train_info(result)
        return None
    
    def find_all(self):
        """Find all train info records"""
        query = "SELECT * FROM train_info"
        results = self.fetch_all(query)
        
        return [self._map_to_train_info(row) for row in results]
    
    def _map_to_train_info(self, row):
        """Map database row to TrainInfo object"""
        train_info = TrainInfo()
        train_info.id = row.get('id')
        train_info.epoch = row.get('epoch')
        train_info.learningRate = row.get('learning_rate')
        train_info.batchSize = row.get('batch_size')
        train_info.mae = row.get('mae')
        train_info.mse = row.get('mse')
        train_info.accuracy = row.get('accuracy')
        train_info.timeTrain = row.get('time_train')
        return train_info