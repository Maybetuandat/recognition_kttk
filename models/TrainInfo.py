from datetime import datetime


class TrainInfo:
    def __init__(self, id=None, epoch=None, learningRate=None, batchSize=None,
                 mae=None, mse=None, accuracy=None,
                 timeTrain=None):
        self.id = id
        self.epoch = epoch
        self.learningRate = learningRate
        self.batchSize = batchSize
        self.mae = mae
        self.mse = mse
        self.accuracy = accuracy
        self.timeTrain = timeTrain

    def to_dict(self):
        train_info_dict = {
            'idInfo': self.idInfo,
            'epoch': self.epoch,
            'learningRate': self.learningRate,
            'batchSize': self.batchSize,
            'mae': self.mae,
            'mse': self.mse,
            'accuracy': self.accuracy,
            'timeTrain': self.timeTrain,
        }
        return train_info_dict


    #deserialization data from json 
    @classmethod
    def from_dict(cls, data):
        train_info = cls()
        train_info.id = data.get('id')
        train_info.epoch = data.get('epoch')
        train_info.learningRate = data.get('learningRate')
        train_info.batchSize = data.get('batchSize')
        train_info.mae = data.get('mae')
        train_info.mse = data.get('mse')
        train_info.accuracy = data.get('accuracy')
        train_info.timeTrain = data.get('timeTrain')
        return train_info
