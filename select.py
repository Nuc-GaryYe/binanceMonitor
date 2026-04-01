#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合约筛选策略模块
"""


class SelectStrategy:
    """筛选策略基类"""
    def __init__(self, name, description):
        self.name = name
        self.description = description
    
    def check(self, klines):
        """检查是否符合条件"""
        raise NotImplementedError
    
    def get_high_low(self, klines):
        """获取最高价和最低价"""
        if not klines:
            return 0, 0
        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]
        return max(highs), min(lows)


class RiseFromLowStrategy(SelectStrategy):
    """从最低点上涨策略"""
    def __init__(self, threshold=0.30):
        super().__init__(
            f"从最低点上涨{int(threshold*100)}%",
            f"筛选从最低点上涨超过{int(threshold*100)}%的合约"
        )
        self.threshold = threshold
    
    def check(self, klines):
        """检查是否从最低点上涨超过阈值"""
        if len(klines) < 2:
            return False, 0
        
        high, low = self.get_high_low(klines)
        current_price = float(klines[-1][4])  # 当前收盘价
        
        if low == 0:
            return False, 0
        
        # 计算从最低点的涨幅
        rise_rate = (current_price - low) / low
        
        return rise_rate >= self.threshold, rise_rate


class FallFromHighStrategy(SelectStrategy):
    """从最高点下跌策略"""
    def __init__(self, threshold=0.30):
        super().__init__(
            f"从最高点下跌{int(threshold*100)}%",
            f"筛选从最高点下跌超过{int(threshold*100)}%的合约"
        )
        self.threshold = threshold
    
    def check(self, klines):
        """检查是否从最高点下跌超过阈值"""
        if len(klines) < 2:
            return False, 0
        
        high, low = self.get_high_low(klines)
        current_price = float(klines[-1][4])  # 当前收盘价
        
        if high == 0:
            return False, 0
        
        # 计算从最高点的跌幅
        fall_rate = (high - current_price) / high
        
        return fall_rate >= self.threshold, fall_rate


class VolatilityStrategy(SelectStrategy):
    """震荡幅度策略"""
    def __init__(self, threshold=0.30):
        super().__init__(
            f"震荡幅度超过{int(threshold*100)}%",
            f"筛选震荡幅度超过{int(threshold*100)}%的合约"
        )
        self.threshold = threshold
    
    def check(self, klines):
        """检查震荡幅度是否超过阈值"""
        if len(klines) < 2:
            return False, 0
        
        high, low = self.get_high_low(klines)
        
        if low == 0:
            return False, 0
        
        # 计算震荡幅度
        volatility = (high - low) / low
        
        return volatility >= self.threshold, volatility


# 筛选策略注册表
SELECT_STRATEGIES = {
    "从最低点上涨30%": RiseFromLowStrategy(0.30),
    "从最高点下跌30%": FallFromHighStrategy(0.30),
    "震荡幅度超过30%": VolatilityStrategy(0.30)
}


def get_select_strategy(strategy_name):
    """获取筛选策略实例"""
    return SELECT_STRATEGIES.get(strategy_name)
