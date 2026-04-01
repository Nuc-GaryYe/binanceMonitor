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


class BinanceMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Binance合约价格监控")
        self.root.geometry("600x400")
        
        self.is_running = False
        self.update_interval = 2  # 更新间隔（秒）
        
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
        price_frame = ttk.LabelFrame(self.root, text="实时价格", padding="20")
        price_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.price_label = ttk.Label(price_frame, text="--", font=("Arial", 36, "bold"))
        self.price_label.pack(pady=20)
        
        self.info_label = ttk.Label(price_frame, text="等待开始...", font=("Arial", 10))
        self.info_label.pack()
        
        # 状态栏
        self.status_label = ttk.Label(self.root, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
        
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
    
    def update_price(self):
        """更新价格显示"""
        while self.is_running:
            try:
                symbol = self.symbol_entry.get().upper()
                price = self.get_futures_price(symbol)
                
                current_time = datetime.now().strftime("%H:%M:%S")
                
                self.price_label.config(text=f"${price:,.2f}")
                self.info_label.config(text=f"{symbol} | 更新时间: {current_time}")
                self.status_label.config(text=f"监控中... | 最后更新: {current_time}")
                
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
