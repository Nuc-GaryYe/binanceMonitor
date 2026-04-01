#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Binance合约实时价格监控工具
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
import time
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from collections import deque


class BinanceMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Binance合约价格监控")
        self.root.geometry("1000x700")
        
        self.is_running = False
        self.update_interval = 1  # 更新间隔（秒）
        self.klines = deque(maxlen=60)  # 保存最近60根K线
        
        self.setup_ui()
        
    def setup_ui(self):
        # 顶部输入框架
        input_frame = ttk.Frame(self.root, padding="10")
        input_frame.pack(fill=tk.X)
        
        ttk.Label(input_frame, text="交易对:").pack(side=tk.LEFT)
        self.symbol_entry = ttk.Entry(input_frame, width=20)
        self.symbol_entry.insert(0, "BTCUSDT")
        self.symbol_entry.pack(side=tk.LEFT, padx=5)
        
        self.start_btn = ttk.Button(input_frame, text="开始监控", command=self.start_monitoring)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(input_frame, text="停止监控", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)
        
        # 价格显示框架
        price_frame = ttk.LabelFrame(self.root, text="实时价格", padding="10")
        price_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.price_label = ttk.Label(price_frame, text="--", font=("Arial", 24, "bold"))
        self.price_label.pack(side=tk.LEFT, padx=20)
        
        self.info_label = ttk.Label(price_frame, text="等待开始...", font=("Arial", 10))
        self.info_label.pack(side=tk.LEFT)
        
        # K线图框架
        chart_frame = ttk.LabelFrame(self.root, text="1分钟K线图", padding="10")
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建matplotlib图表
        self.fig = Figure(figsize=(10, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 状态栏
        self.status_label = ttk.Label(self.root, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
        
    def get_klines(self, symbol, limit=60):
        """获取K线数据"""
        try:
            url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=1m&limit={limit}"
            proxies = {
                'http': 'http://127.0.0.1:7890',
                'https': 'http://127.0.0.1:7890'
            }
            response = requests.get(url, proxies=proxies, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"获取K线数据失败: {str(e)}")
    
    def get_futures_price(self, symbol):
        """获取Binance合约价格"""
        try:
            url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}"
            proxies = {
                'http': 'http://127.0.0.1:7890',
                'https': 'http://127.0.0.1:7890'
            }
            response = requests.get(url, proxies=proxies, timeout=5)
            response.raise_for_status()
            data = response.json()
            return float(data['price'])
        except Exception as e:
            raise Exception(f"获取价格失败: {str(e)}")
    
    def draw_candlestick(self):
        """绘制蜡烛图"""
        if len(self.klines) == 0:
            return
            
        self.ax.clear()
        
        times = []
        opens = []
        highs = []
        lows = []
        closes = []
        
        for kline in self.klines:
            times.append(datetime.fromtimestamp(kline[0] / 1000))
            opens.append(float(kline[1]))
            highs.append(float(kline[2]))
            lows.append(float(kline[3]))
            closes.append(float(kline[4]))
        
        # 绘制蜡烛图
        for i in range(len(times)):
            color = 'green' if closes[i] >= opens[i] else 'red'
            
            # 绘制影线
            self.ax.plot([times[i], times[i]], [lows[i], highs[i]], color=color, linewidth=1)
            
            # 绘制实体
            height = abs(closes[i] - opens[i])
            bottom = min(opens[i], closes[i])
            self.ax.bar(times[i], height, bottom=bottom, width=0.0006, color=color, alpha=0.8)
        
        self.ax.set_xlabel('时间')
        self.ax.set_ylabel('价格 (USDT)')
        self.ax.grid(True, alpha=0.3)
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        self.fig.autofmt_xdate()
        
        self.canvas.draw()
    
    def update_price(self):
        """更新价格显示"""
        while self.is_running:
            try:
                symbol = self.symbol_entry.get().upper()
                
                # 获取K线数据
                klines_data = self.get_klines(symbol)
                self.klines = deque(klines_data, maxlen=60)
                
                # 获取当前价格
                price = self.get_futures_price(symbol)
                
                current_time = datetime.now().strftime("%H:%M:%S")
                
                self.price_label.config(text=f"${price:,.2f}")
                self.info_label.config(text=f"{symbol} | 更新时间: {current_time}")
                self.status_label.config(text=f"监控中... | 最后更新: {current_time}")
                
                # 更新K线图
                self.draw_candlestick()
                
            except Exception as e:
                self.status_label.config(text=f"错误: {str(e)}")
                
            time.sleep(self.update_interval)
    
    def start_monitoring(self):
        """开始监控"""
        if not self.symbol_entry.get().strip():
            messagebox.showwarning("警告", "请输入交易对符号")
            return
            
        self.is_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.symbol_entry.config(state=tk.DISABLED)
        
        # 在新线程中运行更新
        self.monitor_thread = threading.Thread(target=self.update_price, daemon=True)
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.symbol_entry.config(state=tk.NORMAL)
        self.status_label.config(text="已停止")


def main():
    root = tk.Tk()
    app = BinanceMonitor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
