# Ví dụ sử dụng
from dao import ModelDAO, DetectionDAO
from models.Detection import Detection
from models.Model import Model

# Tạo model mới
model_dao = ModelDAO()
model = Model(name="YOLOv8", version="1.0", description="Fraud detection model")
model_id = model_dao.insert(model)

# Tìm kiếm
all_models = model_dao.find_all()
latest_model = model_dao.find_latest_version("YOLOv8")

# Detection
detection_dao = DetectionDAO()
detection = Detection(model=model, description="Test detection")
detection_dao.insert(detection)