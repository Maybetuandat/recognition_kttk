# services/__init__.py

from .BaseService import BaseService
from .TrainInfoService import TrainInfoService
from .ModelService import ModelService
from .DetectionService import DetectionService
from .FraudLabelService import FraudLabelService


__all__ = [
    'BaseService',
    'TrainInfoService',
    'ModelService',
    'DetectionService',
    'FraudLabelService'
]