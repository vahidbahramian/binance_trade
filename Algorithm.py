import abc

class OfflineAlgorithm(abc.ABC):
        @abc.abstractmethod
        def __init__(self):
            pass

        @abc.abstractmethod
        def RunAlgorithm(self):
            pass

        @abc.abstractmethod
        def CheckStrategy(self):
            pass

        # @abc.abstractmethod
        # def CheckProfitOrLoss(self):
        #     pass

        @abc.abstractmethod
        def WriteResult(self):
            pass