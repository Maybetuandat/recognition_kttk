# services/__init__.py

from .BaseService import BaseService
from .ModelService import ModelService

from .FraudLabelService import FraudLabelService
from .VideoDetectionService import VideoDetectionService
from .FileStorageService import FileStorageService
from .BoundingBoxDetectionService import BoundingBoxDetectionService
from .FrameDetectionService import FrameDetectionService
from .PhaseDetectionService import PhaseDetectionService
__all__ = [
    'BaseService',
    'ModelService',
    'PhaseDetectionService',
    'FraudLabelService',
    'VideoDetectionService',
    'FileStorageService',
    'BoundingBoxDetectionService',
    'FrameDetectionService'
]