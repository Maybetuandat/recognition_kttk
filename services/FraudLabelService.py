import requests
from models.FraudLabel import FraudLabel


class FraudLabelService:
    def __init__(self):
        self.base_url = "http://localhost:8888/api/fraud-label"
    
    def get_all(self):
        """Get all fraud labels from Java backend"""
        try:
            response = requests.get(self.base_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            print(f"fetch data from backend server java : ", data)
            return [FraudLabel.from_dict(item) for item in data]
            
        except Exception as e:
            print(f"Error fetching fraud labels: {e}")
            return []
    
    def get_by_class_id(self, class_id):
        """Get fraud label by class ID from Java backend"""
        try:
            url = f"{self.base_url}/class/{class_id}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 404:
                print(f"FraudLabel with classId {class_id} not found")
                return None
                
            response.raise_for_status()
            
            data = response.json()
            print(f"fetch fraud label by classId {class_id}: ", data)
            # Đảm bảo trả về đối tượng FraudLabel đầy đủ
            return FraudLabel.from_dict(data)
            
        except Exception as e:
            print(f"Error fetching fraud label by classId {class_id}: {e}")
            return None