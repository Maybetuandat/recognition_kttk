
import os
import sys
import shutil
from datetime import datetime

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.ModelService import ModelService
from services.TrainInfoService import TrainInfoService
from config.config import Config


def create_model_directory():
    """Tạo thư mục models nếu chưa có"""
    model_dir = os.path.join(Config.BASE_DIR, 'uploads/models')
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
        print(f"✅ Created models directory: {model_dir}")
    return model_dir


def copy_model_file(src_path, dest_dir, model_name, version):
    """Copy file .pt từ thư mục src sang thư mục models"""
    if not os.path.exists(src_path):
        raise FileNotFoundError(f"Model file not found: {src_path}")
    
    # Tạo tên file đích
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{model_name}_v{version}_{timestamp}.pt"
    dest_path = os.path.join(dest_dir, filename)
    
    # Copy file
    shutil.copy2(src_path, dest_path)
    print(f"✅ Copied model file: {src_path} -> {dest_path}")
    
    # Return relative path cho database
    return os.path.join('models', filename)


def create_sample_models():
    """Tạo các model mẫu với dữ liệu giả"""
    
    model_service = ModelService()
    
    # Danh sách các model mẫu
    sample_models = [
        {
            'name': 'YOLOv8_Fraud_Detection',
            'version': '1.0',
            'description': 'Model phát hiện gian lận sử dụng YOLOv8 - phiên bản đầu tiên',
            'pt_file': 'model.pt',  # Tên file trong thư mục src
            'trainInfo': {
                'epoch': 100,
                'learningRate': 0.001,
                'batchSize': 16,
                'mae': 0.125,
                'mse': 0.089,
                'accuracy': 0.945,
                'timeTrain': '2h 30m 15s'
            }
        },
        {
            'name': 'YOLOv8_Fraud_Detection',
            'version': '1.1',
            'description': 'Model phát hiện gian lận - cải thiện accuracy',
            'pt_file': 'model.pt',  # Cùng file nhưng version khác
            'trainInfo': {
                'epoch': 150,
                'learningRate': 0.0008,
                'batchSize': 32,
                'mae': 0.098,
                'mse': 0.067,
                'accuracy': 0.967,
                'timeTrain': '3h 45m 22s'
            }
        }
    ]
    
    # Tạo thư mục models
    model_dir = create_model_directory()
    
    # Insert từng model
    created_models = []
    
    for model_data in sample_models:
        try:
            print(f"\n🔄 Creating model: {model_data['name']} v{model_data['version']}")
            
            # Đường dẫn file .pt trong thư mục src
            src_file_path = os.path.join(Config.BASE_DIR, model_data['pt_file'])
            
            # Copy file model
            model_url = copy_model_file(
                src_file_path, 
                model_dir, 
                model_data['name'], 
                model_data['version']
            )
            
            # Tạo data để insert
            insert_data = {
                'name': model_data['name'],
                'version': model_data['version'],
                'description': model_data['description'],
                'modelUrl': model_url,
                'trainInfo': model_data['trainInfo']
            }
            
            # Insert vào database
            created_model = model_service.create(insert_data)
            
            print(f"✅ Successfully created model:")
            print(f"   - ID: {created_model.id}")
            print(f"   - Name: {created_model.name}")
            print(f"   - Version: {created_model.version}")
            print(f"   - Accuracy: {created_model.trainInfo.accuracy if created_model.trainInfo else 'N/A'}")
            print(f"   - Model URL: {created_model.modelUrl}")
            
            created_models.append(created_model)
            
        except Exception as e:
            print(f"❌ Failed to create model {model_data['name']} v{model_data['version']}: {str(e)}")
            continue
    
    return created_models


def display_summary(models):
    """Hiển thị tóm tắt các model đã tạo"""
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY - Created {len(models)} models")
    print(f"{'='*60}")
    
    for i, model in enumerate(models, 1):
        accuracy = model.trainInfo.accuracy if model.trainInfo else 0
        print(f"{i}. {model.name} v{model.version}")
        print(f"   └── ID: {model.id} | Accuracy: {accuracy:.1%} | URL: {model.modelUrl}")
    
    print(f"\n🎉 All models have been successfully inserted into the database!")


def main():
    """Main function"""
    print("🚀 Starting model insertion process...")
    print(f"📁 Base directory: {Config.BASE_DIR}")
    
    try:
        # Kiểm tra file .pt có tồn tại không
        src_file = os.path.join(Config.BASE_DIR, 'model.pt')
        if not os.path.exists(src_file):
            print(f"❌ Model file not found: {src_file}")
            print("📝 Please make sure 'model.pt' exists in the 'src' directory")
            return
        
        print(f"✅ Found model file: {src_file}")
        
        # Tạo các model mẫu
        created_models = create_sample_models()
        
        if created_models:
            display_summary(created_models)
        else:
            print("❌ No models were created successfully")
    
    except Exception as e:
        print(f"💥 Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()