from abc import ABC, abstractmethod
import pandas as pd
import pandas_ta as ta

class BaseStrategy(ABC):
    def __init__(self, params=None):
        """
        初始化策略参数
        params: dict, 例如 {'ma_period': 14, 'rsi_upper': 70}
        """
        self.params = params or {}

    @abstractmethod
    def add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标，必须返回带有新列的 DataFrame
        """
        pass

    @abstractmethod
    def on_bar(self, df: pd.DataFrame, i: int) -> dict:
        """
        K线走完时的逻辑
        df: 全量数据
        i: 当前K线索引 (用于回测时防未来函数)
        
        Return:
        {
            'signal': 'LONG' | 'SHORT' | None,
            'stop_loss': float,
            'take_profit': float,
            'reason': str
        }
        """
        pass
