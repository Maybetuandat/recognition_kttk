import mysql.connector
from mysql.connector import Error
from abc import ABC, abstractmethod
from config.config import Config


class BaseDAO(ABC):
    def __init__(self):
        self.config = {
            'host': Config.DB_HOST,
            'port': Config.DB_PORT,
            'database': Config.DB_NAME,
            'user': Config.DB_USER,
            'password': Config.DB_PASSWORD
        }
    
    def get_connection(self):
        try:
            connection = mysql.connector.connect(**self.config)
            return connection
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return None
    
    def execute_query(self, query, params=None):
        connection = self.get_connection()
        if not connection:
            return False
        try:
            cursor = connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            connection.commit()
            if query.strip().upper().startswith('INSERT'):
                return cursor.lastrowid
            return True
            
        except Error as e:
            print(f"Error executing query: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
            connection.close()
    
    def fetch_all(self, query, params=None):
        connection = self.get_connection()
        if not connection:
            return []
        
        try:
            cursor = connection.cursor(dictionary=True)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
        except Error as e:
            print(f"Error fetching data: {e}")
            return []
        finally:
            cursor.close()
            connection.close()
    
    def fetch_one(self, query, params=None):
        connection = self.get_connection()
        if not connection:
            return None
        
        try:
            cursor = connection.cursor(dictionary=True)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchone()
        except Error as e:
            print(f"Error fetching data: {e}")
            return None
        finally:
            cursor.close()
            connection.close()
    
    @abstractmethod
    def create_table(self):
        """Create table if not exists"""
        pass
    
    @abstractmethod
    def insert(self, obj):
        """Insert a new record"""
        pass
    
    @abstractmethod
    def update(self, obj):
        """Update an existing record"""
        pass
    
    @abstractmethod
    def delete(self, id):
        """Delete a record by id"""
        pass
    
    @abstractmethod
    def find_by_id(self, id):
        """Find a record by id"""
        pass
    
    @abstractmethod
    def find_all(self):
        """Find all records"""
        pass