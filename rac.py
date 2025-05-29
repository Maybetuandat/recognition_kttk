# def _export_results_to_json(self, results, frame_count):
    #     """Export YOLO results to JSON format"""
    #     import json
        
    #     # Kiểm tra nếu có detection
    #     if results[0].boxes is None:
    #         detection_data = {
    #             'frame_number': frame_count,
    #             'detections_count': 0,
    #             'boxes': []
    #         }
    #     else:
    #         # Extract data từ results
    #         boxes_data = []
            
    #         # Cách 1: Duyệt qua từng box
    #         for i, box in enumerate(results[0].boxes):
    #             box_info = {
    #                 'detection_id': i,
    #                 'xyxy': box.xyxy[0].tolist(),  # [x1, y1, x2, y2]
    #                 'xywh': box.xywh[0].tolist() if hasattr(box, 'xywh') else None,  # [x, y, w, h]
    #                 'confidence': float(box.conf[0]),
    #                 'class_id': int(box.cls[0]),
    #                 'class_name': self.yolo_model.names[int(box.cls[0])] if hasattr(self, 'yolo_model') else f"class_{int(box.cls[0])}"
    #             }
    #             boxes_data.append(box_info)
            
    #         # Hoặc Cách 2: Lấy tất cả cùng lúc
    #         all_xyxy = results[0].boxes.xyxy.tolist()  # List of [x1, y1, x2, y2]
    #         all_conf = results[0].boxes.conf.tolist()  # List of confidences
    #         all_cls = results[0].boxes.cls.tolist()    # List of class ids
            
    #         detection_data = {
    #             'frame_number': frame_count,
    #             'detections_count': len(results[0].boxes),
    #             'boxes': boxes_data,
    #             'raw_data': {
    #                 'all_xyxy': all_xyxy,
    #                 'all_confidences': all_conf,
    #                 'all_class_ids': all_cls
    #             }
    #         }
        
    #     # Thêm thông tin khác nếu có
    #     detection_data['image_shape'] = results[0].orig_shape if hasattr(results[0], 'orig_shape') else None
        
    #     # In ra màn hình
    #     print(f"\n=== Frame {frame_count} Detection Results ===")
    #     print(json.dumps(detection_data, indent=2))
        
    #     # Lưu vào file
    #     output_dir = "detection_outputs"
    #     os.makedirs(output_dir, exist_ok=True)
        
    #     # Lưu từng frame
    #     frame_file = os.path.join(output_dir, f"frame_{frame_count:06d}_detections.json")
    #     with open(frame_file, 'w') as f:
    #         json.dump(detection_data, f, indent=2)
        
    #     # Hoặc append vào file tổng hợp
    #     summary_file = os.path.join(output_dir, f"detection_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl")
    #     with open(summary_file, 'a') as f:
    #         f.write(json.dumps(detection_data) + '\n')