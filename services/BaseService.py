from abc import ABC, abstractmethod


class BaseService(ABC):
    """Base service class with common functionality"""
    
    def __init__(self):
        self.dao = None
    
    @abstractmethod
    def create(self, data):
        """Create a new record"""
        pass
    
    @abstractmethod
    def update(self, id, data):
        """Update an existing record"""
        pass
    
    @abstractmethod
    def delete(self, id):
        """Delete a record"""
        pass
    
    @abstractmethod
    def get_by_id(self, id):
        """Get a record by ID"""
        pass
    
    @abstractmethod
    def get_all(self):
        """Get all records"""
        pass
    
    def validate_data(self, data, required_fields=None):
        """Validate input data"""
        if not data:
            raise ValueError("Data cannot be empty")
        
        if required_fields:
            missing_fields = []
            for field in required_fields:
                if field not in data or data[field] is None:
                    missing_fields.append(field)
            
            if missing_fields:
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        return True