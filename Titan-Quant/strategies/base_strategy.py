from abc import ABC, abstractmethod
import pandas as pd
import pandas_ta as ta

class BaseStrategy(ABC):
    def __init__(self, params=None):
        self.params = params or {}

    @abstractmethod
    def add_indicators(self, df):
        """在这里计算技术指标"""
        pass

    @abstractmethod
    def on_bar(self, df):
        """
        每一根K线走完后的逻辑
        返回: dict {'signal': 'LONG'/'SHORT'/None, 'sl': float, 'tp': float, 'reason': str}
        """
        pass