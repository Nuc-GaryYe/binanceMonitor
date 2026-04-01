#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测引擎
"""

from datetime import datetime


class BacktestEngine:
    """回测引擎"""
    def __init__(self, initial_capital=10000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = 0  # 持仓数量
        self.trades = []  # 交易记录
        
    def run(self, klines, buy_strategy, sell_strategy):
        """运行回测"""
        self.capital = self.initial_capital
        self.position = 0
        self.trades = []
        
        for i in range(60, len(klines)):
            current_klines = klines[:i+1]
            current_price = float(klines[i][4])  # 收盘价
            current_time = datetime.fromtimestamp(klines[i][0] / 1000)
            
            # 检查买入信号
            if self.position == 0 and buy_strategy.should_buy(current_klines):
                # 全仓买入
                self.position = self.capital / current_price
                self.trades.append({
                    'time': current_time,
                    'type': 'BUY',
                    'price': current_price,
                    'amount': self.position,
                    'capital': self.capital
                })
                self.capital = 0
            
            # 检查卖出信号
            elif self.position > 0 and sell_strategy.should_sell(current_klines):
                # 全部卖出
                self.capital = self.position * current_price
                self.trades.append({
                    'time': current_time,
                    'type': 'SELL',
                    'price': current_price,
                    'amount': self.position,
                    'capital': self.capital
                })
                self.position = 0
        
        # 计算最终收益
        final_value = self.capital if self.position == 0 else self.position * float(klines[-1][4])
        profit = final_value - self.initial_capital
        profit_rate = (profit / self.initial_capital) * 100
        
        return {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'profit': profit,
            'profit_rate': profit_rate,
            'trades': self.trades,
            'total_trades': len(self.trades)
        }
