#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易策略模块
"""

class Strategy:
    """策略基类"""
    def __init__(self, name):
        self.name = name
    
    def should_buy(self, klines):
        """判断是否买入"""
        raise NotImplementedError
    
    def should_sell(self, klines):
        """判断是否卖出"""
        raise NotImplementedError
    
    def calculate_ma(self, klines, period):
        """计算移动平均线"""
        if len(klines) < period:
            return None
        closes = [float(k[4]) for k in klines[-period:]]
        return sum(closes) / period


class MA5_60Strategy(Strategy):
    """5日均线和60日均线交叉策略"""
    def __init__(self):
        super().__init__("MA5/60交叉策略")
        self.last_ma5 = None
        self.last_ma60 = None
    
    def should_buy(self, klines):
        """金叉：MA5上穿MA60"""
        if len(klines) < 60:
            return False
        
        ma5 = self.calculate_ma(klines, 5)
        ma60 = self.calculate_ma(klines, 60)
        
        if ma5 is None or ma60 is None:
            return False
        
        # 检测上穿
        if self.last_ma5 is not None and self.last_ma60 is not None:
            if self.last_ma5 <= self.last_ma60 and ma5 > ma60:
                self.last_ma5 = ma5
                self.last_ma60 = ma60
                return True
        
        self.last_ma5 = ma5
        self.last_ma60 = ma60
        return False
    
    def should_sell(self, klines):
        """死叉：MA5下穿MA60"""
        if len(klines) < 60:
            return False
        
        ma5 = self.calculate_ma(klines, 5)
        ma60 = self.calculate_ma(klines, 60)
        
        if ma5 is None or ma60 is None:
            return False
        
        # 检测下穿
        if self.last_ma5 is not None and self.last_ma60 is not None:
            if self.last_ma5 >= self.last_ma60 and ma5 < ma60:
                self.last_ma5 = ma5
                self.last_ma60 = ma60
                return True
        
        self.last_ma5 = ma5
        self.last_ma60 = ma60
        return False


class MA10_60Strategy(Strategy):
    """10日均线和60日均线交叉策略"""
    def __init__(self):
        super().__init__("MA10/60交叉策略")
        self.last_ma10 = None
        self.last_ma60 = None
    
    def should_buy(self, klines):
        """金叉：MA10上穿MA60"""
        if len(klines) < 60:
            return False
        
        ma10 = self.calculate_ma(klines, 10)
        ma60 = self.calculate_ma(klines, 60)
        
        if ma10 is None or ma60 is None:
            return False
        
        # 检测上穿
        if self.last_ma10 is not None and self.last_ma60 is not None:
            if self.last_ma10 <= self.last_ma60 and ma10 > ma60:
                self.last_ma10 = ma10
                self.last_ma60 = ma60
                return True
        
        self.last_ma10 = ma10
        self.last_ma60 = ma60
        return False
    
    def should_sell(self, klines):
        """死叉：MA10下穿MA60"""
        if len(klines) < 60:
            return False
        
        ma10 = self.calculate_ma(klines, 10)
        ma60 = self.calculate_ma(klines, 60)
        
        if ma10 is None or ma60 is None:
            return False
        
        # 检测下穿
        if self.last_ma10 is not None and self.last_ma60 is not None:
            if self.last_ma10 >= self.last_ma60 and ma10 < ma60:
                self.last_ma10 = ma10
                self.last_ma60 = ma60
                return True
        
        self.last_ma10 = ma10
        self.last_ma60 = ma60
        return False


# 策略注册表
STRATEGIES = {
    "MA5/60交叉": MA5_60Strategy,
    "MA10/60交叉": MA10_60Strategy
}


def get_strategy(strategy_name):
    """获取策略实例"""
    if strategy_name in STRATEGIES:
        return STRATEGIES[strategy_name]()
    return None
