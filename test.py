import os
from services.ModelService import ModelService
from config.config import Config # Giả sử Config đã được cấu hình đúng

# THAY THẾ ID NÀY BẰNG ID CỦA MỘT MODEL CÓ THẬT TRONG DATABASE CỦA BẠN
# VÀ FILE MODEL CỦA NÓ (.pt) PHẢI TỒN TẠI ĐÚNG ĐƯỜNG DẪN
TARGET_MODEL_ID = 1 # <<<<----- THAY ĐỔI ID NÀY

def quick_test_load_model_and_get_classes(model_id_to_test):
    print(f"--- Bắt đầu kiểm tra nhanh cho Model ID: {model_id_to_test} ---")
    
    # Khởi tạo ModelService
    # Lưu ý: Điều này sẽ kết nối tới cơ sở dữ liệu thật của bạn
    # và sử dụng các đường dẫn file thật từ Config.
    try:
        model_service = ModelService()
    except Exception as e:
        print(f"LỖI khi khởi tạo ModelService: {e}")
        return

    try:
        # Load model
        print(f"Đang tải model với ID: {model_id_to_test}...")
        loaded_data = model_service.load_model(model_id_to_test)
        
        if not loaded_data:
            print(f"Không thể tải model với ID: {model_id_to_test}. Dữ liệu trả về rỗng.")
            return

        yolo_model = loaded_data.get('model')
        model_info = loaded_data.get('info')

        if not yolo_model:
            print("Không tìm thấy 'model' trong dữ liệu trả về.")
            return
        
        if not model_info:
            print("Không tìm thấy 'info' (thông tin model từ DB) trong dữ liệu trả về.")
            # Vẫn có thể tiếp tục để xem class nếu yolo_model có
        else:
            print(f"\nThông tin model từ cơ sở dữ liệu:")
            print(f"  ID: {model_info.id}")
            print(f"  Tên: {model_info.name}")
            print(f"  Phiên bản: {model_info.version}")
            print(f"  Đường dẫn file (modelUrl): {model_info.modelUrl}")
            actual_path = os.path.join(Config.BASE_DIR, model_info.modelUrl)
            print(f"  Đường dẫn tuyệt đối dự kiến: {actual_path}")
            if os.path.exists(actual_path):
                print("  Trạng thái file trên đĩa: TỒN TẠI")
            else:
                print("  Trạng thái file trên đĩa: KHÔNG TỒN TẠI - Model có thể không load được!")


        # Lấy và hiển thị các class
        if hasattr(yolo_model, 'names'):
            class_names = yolo_model.names
            print("\nCác lớp (classes) trong model đã load:")
            if isinstance(class_names, dict):
                for class_id, name in class_names.items():
                    print(f"  ID: {class_id}, Tên: {name}")
            elif isinstance(class_names, list):
                for i, name in enumerate(class_names):
                    print(f"  ID: {i}, Tên: {name}")
            else:
                print(f"  Không thể xác định định dạng của 'names': {type(class_names)}")
            
            if not class_names:
                 print("  Model đã load nhưng không có thông tin class (names rỗng).")

        else:
            print("\nModel YOLO đã load không có thuộc tính 'names'. Không thể lấy danh sách class.")
            print(f"Kiểu của đối tượng model: {type(yolo_model)}")
            print("Thử kiểm tra các thuộc tính khác nếu có (ví dụ: model.model.names cho một số cấu trúc lồng nhau).")

        print(f"\n--- Kết thúc kiểm tra nhanh cho Model ID: {model_id_to_test} ---")

    except FileNotFoundError as e:
        print(f"LỖI FileNotFoundError: {e}. Kiểm tra lại đường dẫn modelUrl trong DB và sự tồn tại của file.")
    except ValueError as e:
        print(f"LỖI ValueError: {e}. Có thể model_id không tồn tại hoặc model không có modelUrl.")
    except Exception as e:
        print(f"LỖI không xác định khi tải hoặc xử lý model: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    if TARGET_MODEL_ID is None:
        print("Vui lòng đặt giá trị cho TARGET_MODEL_ID ở đầu file script.")
    else:
        quick_test_load_model_and_get_classes(TARGET_MODEL_ID)