from flask import jsonify
from services.ModelService import ModelService


class ModelController:
    def __init__(self):
        self.model_service = ModelService()
    
    def get_all_models(self):
        try:
            models = self.model_service.get_all()
            
            # Convert to dict format
            models_data = []
            for model in models:
                model_dict = model.to_dict()
                # Add train info if available
                if model.trainInfo:
                    model_dict['accuracy'] = model.trainInfo.accuracy
                    model_dict['trainInfo'] = model.trainInfo.to_dict()
                models_data.append(model_dict)
            
            return jsonify(
                models_data
            ), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def register_routes(self, app):
        """Register routes with Flask app"""
        app.add_url_rule('/api/models', 'get_all_models', self.get_all_models, methods=['GET'])