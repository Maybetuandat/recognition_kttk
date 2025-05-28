import mysql.connector
from config.config import Config

class BaseDAO:
    def __init__(self):
        self.config = {
            'host': Config.DB_HOST,
            'port': Config.DB_PORT,
            'user': Config.DB_USER,
            'password': Config.DB_PASSWORD,
            'database': Config.DB_NAME
        }
    
    def get_connection(self):
        """Establish and return a database connection."""
        try:
            connection = mysql.connector.connect(**self.config)
            return connection
        except mysql.connector.Error as error:
            print(f"Error connecting to database: {error}")
            raise
    
    def execute_query(self, query, params=None, fetch=True, many=False):
        """Execute a query and optionally fetch results."""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            
            if many and params:
                cursor.executemany(query, params)
            else:
                cursor.execute(query, params or ())
            
            if fetch:
                if many:
                    return cursor.fetchall()
                else:
                    return cursor.fetchone()
            else:
                connection.commit()
                if cursor.lastrowid:
                    return cursor.lastrowid
                return cursor.rowcount
        except mysql.connector.Error as error:
            if connection:
                connection.rollback()
            print(f"Error executing query: {error}")
            print(f"Query: {query}")
            print(f"Params: {params}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    
    def get_by_id(self, table, id, model_class=None):
        """Get a record by ID from the specified table."""
        query = f"SELECT * FROM {table} WHERE id = %s"
        result = self.execute_query(query, (id,), fetch=True, many=False)
        
        if result and model_class:
            return model_class.from_dict(result)
        return result
    
    def get_all(self, table, model_class=None, where_clause=None, params=None, order_by=None, limit=None):
        """Get all records from the specified table with optional filters."""
        query = f"SELECT * FROM {table}"
        
        if where_clause:
            query += f" WHERE {where_clause}"
        
        if order_by:
            query += f" ORDER BY {order_by}"
        
        if limit:
            query += f" LIMIT {limit}"
        
        results = self.execute_query(query, params, fetch=True, many=True)
        
        if results and model_class:
            return [model_class.from_dict(result) for result in results]
        return results
    
    def create(self, table, data):
        """Insert a new record into the specified table."""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        values = tuple(data.values())
        
        return self.execute_query(query, values, fetch=False)
    
    def update(self, table, data, id_field='id'):
        """Update a record in the specified table."""
        id_value = data.pop(id_field)
        
        set_clause = ', '.join([f"{column} = %s" for column in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {id_field} = %s"
        
        values = list(data.values())
        values.append(id_value)  # Add ID value as the last parameter
        
        return self.execute_query(query, tuple(values), fetch=False)
    
    def delete(self, table, id):
        """Delete a record from the specified table by ID."""
        query = f"DELETE FROM {table} WHERE id = %s"
        return self.execute_query(query, (id,), fetch=False)