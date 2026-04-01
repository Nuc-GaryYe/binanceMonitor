#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测引擎
"""

from datetime import datetime


class BacktestEngine:
    """回测引擎 - 支持5倍杠杆做多做空"""
    def __init__(self, initial_capital=10000, leverage=5):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.leverage = leverage  # 杠杆倍数
        self.position = 0  # 持仓数量（正数做多，负数做空）
        self.position_type = None  # 'LONG' 或 'SHORT'
        self.entry_price = 0  # 开仓价格
        self.trades = []  # 交易记录
        self.liquidation_threshold = 0.15  # 爆仓阈值15%
        
    def run(self, klines, long_strategy, close_long_strategy, short_strategy, close_short_strategy):
        """运行回测"""
        self.capital = self.initial_capital
        self.position = 0
        self.position_type = None
        self.entry_price = 0
        self.trades = []
        
        for i in range(60, len(klines)):
            current_klines = klines[:i+1]
            current_price = float(klines[i][4])  # 收盘价
            current_time = datetime.fromtimestamp(klines[i][0] / 1000)
            
            # 检查是否爆仓
            if self.position_type and self.check_liquidation(current_price):
                self.liquidate(current_price, current_time)
                continue
            
            # 无持仓时检查开仓信号
            if self.position_type is None:
                # 检查做多信号
                if long_strategy.should_buy(current_klines):
                    self.open_long(current_price, current_time)
                # 检查做空信号
                elif short_strategy.should_sell(current_klines):
                    self.open_short(current_price, current_time)
            
            # 持有多单时检查平多信号
            elif self.position_type == 'LONG':
                if close_long_strategy.should_sell(current_klines):
                    self.close_long(current_price, current_time)
            
            # 持有空单时检查平空信号
            elif self.position_type == 'SHORT':
                if close_short_strategy.should_buy(current_klines):
                    self.close_short(current_price, current_time)
        
        # 计算最终收益
        if self.position_type:
            # 如果还有持仓，按最后价格平仓
            final_price = float(klines[-1][4])
            final_time = datetime.fromtimestamp(klines[-1][0] / 1000)
            if self.position_type == 'LONG':
                self.close_long(final_price, final_time)
            else:
                self.close_short(final_price, final_time)
        
        final_value = self.capital
        profit = final_value - self.initial_capital
        profit_rate = (profit / self.initial_capital) * 100
        
        return {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'profit': profit,
            'profit_rate': profit_rate,
            'trades': self.trades,
            'total_trades': len(self.trades),
            'leverage': self.leverage
        }
    
    def open_long(self, price, time):
        """开多单"""
        # 使用全部资金开多单（5倍杠杆）
        position_value = self.capital * self.leverage
        self.position = position_value / price
        self.position_type = 'LONG'
        self.entry_price = price
        
        self.trades.append({
            'time': time,
            'type': '开多',
            'price': price,
            'amount': self.position,
            'capital': self.capital,
            'leverage': self.leverage
        })
    
    def close_long(self, price, time):
        """平多单"""
        # 计算盈亏
        profit = self.position * (price - self.entry_price)
        self.capital += profit
        
        self.trades.append({
            'time': time,
            'type': '平多',
            'price': price,
            'amount': self.position,
            'capital': self.capital,
            'profit': profit
        })
        
        self.position = 0
        self.position_type = None
        self.entry_price = 0
    
    def open_short(self, price, time):
        """开空单"""
        # 使用全部资金开空单（5倍杠杆）
        position_value = self.capital * self.leverage
        self.position = position_value / price
        self.position_type = 'SHORT'
        self.entry_price = price
        
        self.trades.append({
            'time': time,
            'type': '开空',
            'price': price,
            'amount': self.position,
            'capital': self.capital,
            'leverage': self.leverage
        })
    
    def close_short(self, price, time):
        """平空单"""
        # 计算盈亏（做空时价格下跌盈利）
        profit = self.position * (self.entry_price - price)
        self.capital += profit
        
        self.trades.append({
            'time': time,
            'type': '平空',
            'price': price,
            'amount': self.position,
            'capital': self.capital,
            'profit': profit
        })
        
        self.position = 0
        self.position_type = None
        self.entry_price = 0
    
    def check_liquidation(self, current_price):
        """检查是否爆仓"""
        if not self.position_type:
            return False
        
        if self.position_type == 'LONG':
            # 做多：价格下跌15%爆仓
            price_change = (current_price - self.entry_price) / self.entry_price
            return price_change <= -self.liquidation_threshold
        else:  # SHORT
            # 做空：价格上涨15%爆仓
            price_change = (current_price - self.entry_price) / self.entry_price
            return price_change >= self.liquidation_threshold
    
    def liquidate(self, price, time):
        """强制平仓（爆仓）"""
        # 爆仓损失全部保证金
        loss = -self.capital
        self.capital = 0
        
        self.trades.append({
            'time': time,
            'type': '爆仓',
            'price': price,
            'amount': self.position,
            'capital': self.capital,
            'profit': loss
        })
        
        self.position = 0
        self.position_type = None
        self.entry_price = 0

