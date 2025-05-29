# dao/__init__.py

from .BaseDAO import BaseDAO
from .TrainInfoDAO import TrainInfoDAO
from .ModelDAO import ModelDAO
from .DetectionDAO import DetectionDAO
from .ResultDetectionDAO import ResultDetectionDAO
from .ResultDetectionFraudDAO import ResultDetectionFraudDAO
__all__ = [
    'BaseDAO',
    'TrainInfoDAO',
    'ModelDAO',
    'DetectionDAO',
    'ResultDetectionDAO',
    'ResultDetectionFraudDAO'
]