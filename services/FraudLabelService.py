import requests
from datetime import datetime
from models.FraudLabel import FraudLabel
from config.config import Config


class FraudLabelService:
    """Service for managing fraud labels from external service"""
    
    def __init__(self):
        # URL của service khác cung cấp fraud labels
        self.external_service_url = Config.FRAUD_LABEL_SERVICE_URL if hasattr(Config, 'FRAUD_LABEL_SERVICE_URL') else None
        self.api_key = Config.FRAUD_LABEL_API_KEY if hasattr(Config, 'FRAUD_LABEL_API_KEY') else None
        
        # Cache fraud labels in memory
        self._cache = {}
        self._cache_timestamp = None
        self._cache_duration = 3600  # 1 hour
    
    def get_all(self):
        """Get all fraud labels from external service or cache"""
        # Check cache first
        if self._is_cache_valid():
            return list(self._cache.values())
        
        # If no external service configured, return mock data
        if not self.external_service_url:
            return self._get_mock_fraud_labels()
        
        try:
            # Call external service
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            response = requests.get(
                f"{self.external_service_url}/fraud-labels",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            fraud_labels = []
            
            for item in data:
                fraud_label = FraudLabel.from_dict(item)
                fraud_labels.append(fraud_label)
                self._cache[fraud_label.id] = fraud_label
            
            self._cache_timestamp = datetime.now()
            return fraud_labels
            
        except Exception as e:
            print(f"Error fetching fraud labels from external service: {e}")
            # Return cached data if available, otherwise mock data
            if self._cache:
                return list(self._cache.values())
            return self._get_mock_fraud_labels()
    
    def get_by_id(self, id):
        """Get a specific fraud label by ID"""
        # Check cache first
        if id in self._cache and self._is_cache_valid():
            return self._cache[id]
        
        # Refresh cache
        fraud_labels = self.get_all()
        
        # Find in refreshed data
        for fraud_label in fraud_labels:
            if fraud_label.id == id:
                return fraud_label
        
        raise ValueError(f"Fraud label with ID {id} not found")
    
    def get_by_class_id(self, class_id):
        """Get fraud label by class ID"""
        fraud_labels = self.get_all()
        
        for fraud_label in fraud_labels:
            if fraud_label.classId == class_id:
                return fraud_label
        
        raise ValueError(f"Fraud label with class ID {class_id} not found")
    
    def get_by_name(self, name):
        """Get fraud label by name"""
        fraud_labels = self.get_all()
        
        for fraud_label in fraud_labels:
            if fraud_label.name.lower() == name.lower():
                return fraud_label
        
        raise ValueError(f"Fraud label with name '{name}' not found")
    
    def search(self, keyword):
        """Search fraud labels by keyword"""
        fraud_labels = self.get_all()
        keyword_lower = keyword.lower()
        
        results = []
        for fraud_label in fraud_labels:
            if keyword_lower in fraud_label.name.lower():
                results.append(fraud_label)
        
        return results
    
    def get_color_mapping(self):
        """Get mapping of class IDs to colors"""
        fraud_labels = self.get_all()
        
        color_map = {}
        for fraud_label in fraud_labels:
            color_map[fraud_label.classId] = fraud_label.color
        
        return color_map
    
    def get_statistics(self):
        """Get statistics about fraud labels"""
        fraud_labels = self.get_all()
        
        return {
            'total_labels': len(fraud_labels),
            'labels_by_class': {label.classId: label.name for label in fraud_labels},
            'color_distribution': self.get_color_mapping(),
            'last_updated': self._cache_timestamp.strftime('%Y-%m-%d %H:%M:%S') if self._cache_timestamp else None
        }
    
    def refresh_cache(self):
        """Force refresh the cache"""
        self._cache.clear()
        self._cache_timestamp = None
        return self.get_all()
    
    def _is_cache_valid(self):
        """Check if cache is still valid"""
        if not self._cache or not self._cache_timestamp:
            return False
        
        age = (datetime.now() - self._cache_timestamp).total_seconds()
        return age < self._cache_duration
    
    def _get_mock_fraud_labels(self):
        """Get mock fraud labels for testing/development"""
        mock_labels = [
            {
                'id': 1,
                'name': 'Fake Logo',
                'classId': 0,
                'color': '#FF0000',
                'createAt': '2024-01-01'
            },
            {
                'id': 2,
                'name': 'Altered Text',
                'classId': 1,
                'color': '#FFA500',
                'createAt': '2024-01-01'
            },
            {
                'id': 3,
                'name': 'Counterfeit Product',
                'classId': 2,
                'color': '#FFFF00',
                'createAt': '2024-01-01'
            },
            {
                'id': 4,
                'name': 'Manipulated Image',
                'classId': 3,
                'color': '#00FF00',
                'createAt': '2024-01-01'
            },
            {
                'id': 5,
                'name': 'Forged Document',
                'classId': 4,
                'color': '#0000FF',
                'createAt': '2024-01-01'
            },
            {
                'id': 6,
                'name': 'Suspicious Pattern',
                'classId': 5,
                'color': '#800080',
                'createAt': '2024-01-01'
            }
        ]
        
        fraud_labels = []
        for item in mock_labels:
            fraud_label = FraudLabel.from_dict(item)
            fraud_labels.append(fraud_label)
            self._cache[fraud_label.id] = fraud_label
        
        self._cache_timestamp = datetime.now()
        return fraud_labels