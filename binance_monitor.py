#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Binance合约实时价格监控工具
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import requests
import threading
import time
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from collections import deque
from strategy import get_strategy, STRATEGIES
from backtest import BacktestEngine
import websocket
import json
from config import Config


class BinanceMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Binance合约价格监控与回测系统")
        self.root.geometry("1200x800")
        
        self.is_running = False
        self.update_interval = 1  # 更新间隔（秒）
        self.klines = deque(maxlen=60)  # 保存最近60根K线
        self.price_precision = 2  # 价格精度
        self.ws = None  # WebSocket连接
        self.current_price = 0  # 当前价格
        
        # 加载配置
        self.config = Config()
        
        self.setup_ui()
        self.load_config_to_ui()
        
    def setup_ui(self):
        # 创建Notebook（标签页）
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 实时监控标签页
        monitor_tab = ttk.Frame(notebook)
        notebook.add(monitor_tab, text="实时监控")
        self.setup_monitor_tab(monitor_tab)
        
        # 回测标签页
        backtest_tab = ttk.Frame(notebook)
        notebook.add(backtest_tab, text="策略回测")
        self.setup_backtest_tab(backtest_tab)
        
        # 状态栏
        self.status_label = ttk.Label(self.root, text="就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_monitor_tab(self, parent):
        """设置实时监控标签页"""
        # 顶部输入框架
        input_frame = ttk.Frame(parent, padding="10")
        input_frame.pack(fill=tk.X)
        
        ttk.Label(input_frame, text="交易对:").pack(side=tk.LEFT)
        self.symbol_entry = ttk.Entry(input_frame, width=20)
        self.symbol_entry.pack(side=tk.LEFT, padx=5)
        
        self.start_btn = ttk.Button(input_frame, text="开始监控", command=self.start_monitoring)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(input_frame, text="停止监控", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT)
        
        # 价格显示框架
        price_frame = ttk.LabelFrame(parent, text="实时价格", padding="10")
        price_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.price_label = ttk.Label(price_frame, text="--", font=("Arial", 24, "bold"))
        self.price_label.pack(side=tk.LEFT, padx=20)
        
        self.info_label = ttk.Label(price_frame, text="等待开始...", font=("Arial", 10))
        self.info_label.pack(side=tk.LEFT)
        
        # K线图框架
        chart_frame = ttk.LabelFrame(parent, text="1分钟K线图", padding="10")
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 创建matplotlib图表
        self.fig = Figure(figsize=(10, 5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def setup_backtest_tab(self, parent):
        """设置回测标签页"""
        # 参数设置框架
        param_frame = ttk.LabelFrame(parent, text="回测参数", padding="10")
        param_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 交易对和K线周期
        row1 = ttk.Frame(param_frame)
        row1.pack(fill=tk.X, pady=5)
        ttk.Label(row1, text="交易对:", width=12).pack(side=tk.LEFT)
        self.bt_symbol_entry = ttk.Entry(row1, width=20)
        self.bt_symbol_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row1, text="K线周期:", width=12).pack(side=tk.LEFT, padx=(20, 0))
        self.interval_var = tk.StringVar()
        self.interval_combo = ttk.Combobox(row1, textvariable=self.interval_var,
                                          values=["1m", "3m", "5m", "15m"], width=10, state="readonly")
        self.interval_combo.pack(side=tk.LEFT, padx=5)
        
        # K线数量
        ttk.Label(row1, text="K线数量:", width=12).pack(side=tk.LEFT, padx=(20, 0))
        self.bt_limit_entry = ttk.Entry(row1, width=10)
        self.bt_limit_entry.pack(side=tk.LEFT, padx=5)
        
        # 做多策略
        row2 = ttk.Frame(param_frame)
        row2.pack(fill=tk.X, pady=5)
        ttk.Label(row2, text="做多策略:", width=12).pack(side=tk.LEFT)
        self.long_strategy_var = tk.StringVar()
        self.long_strategy_combo = ttk.Combobox(row2, textvariable=self.long_strategy_var, 
                                                values=list(STRATEGIES.keys()), width=18, state="readonly")
        self.long_strategy_combo.pack(side=tk.LEFT, padx=5)
        
        # 平多策略
        ttk.Label(row2, text="平多策略:", width=12).pack(side=tk.LEFT, padx=(20, 0))
        self.close_long_strategy_var = tk.StringVar()
        self.close_long_strategy_combo = ttk.Combobox(row2, textvariable=self.close_long_strategy_var,
                                                 values=list(STRATEGIES.keys()), width=18, state="readonly")
        self.close_long_strategy_combo.pack(side=tk.LEFT, padx=5)
        
        # 做空策略
        row3 = ttk.Frame(param_frame)
        row3.pack(fill=tk.X, pady=5)
        ttk.Label(row3, text="做空策略:", width=12).pack(side=tk.LEFT)
        self.short_strategy_var = tk.StringVar()
        self.short_strategy_combo = ttk.Combobox(row3, textvariable=self.short_strategy_var,
                                                 values=list(STRATEGIES.keys()), width=18, state="readonly")
        self.short_strategy_combo.pack(side=tk.LEFT, padx=5)
        
        # 平空策略
        ttk.Label(row3, text="平空策略:", width=12).pack(side=tk.LEFT, padx=(20, 0))
        self.close_short_strategy_var = tk.StringVar()
        self.close_short_strategy_combo = ttk.Combobox(row3, textvariable=self.close_short_strategy_var,
                                                       values=list(STRATEGIES.keys()), width=18, state="readonly")
        self.close_short_strategy_combo.pack(side=tk.LEFT, padx=5)
        
        # 初始资金和杠杆
        row4 = ttk.Frame(param_frame)
        row4.pack(fill=tk.X, pady=5)
        ttk.Label(row4, text="初始资金:", width=12).pack(side=tk.LEFT)
        self.capital_entry = ttk.Entry(row4, width=20)
        self.capital_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row4, text="杠杆倍数:", width=12).pack(side=tk.LEFT, padx=(20, 0))
        self.leverage_entry = ttk.Entry(row4, width=10)
        self.leverage_entry.pack(side=tk.LEFT, padx=5)
        
        # 全仓选项
        row5 = ttk.Frame(param_frame)
        row5.pack(fill=tk.X, pady=5)
        self.full_position_var = tk.BooleanVar(value=True)
        self.full_position_check = ttk.Checkbutton(row5, text="全仓模式", variable=self.full_position_var)
        self.full_position_check.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row5, text="(取消勾选则使用固定仓位，每次开仓使用初始资金)", font=("Arial", 9)).pack(side=tk.LEFT, padx=5)
        
        # 开始回测按钮
        self.backtest_btn = ttk.Button(row5, text="开始回测", command=self.run_backtest)
        self.backtest_btn.pack(side=tk.LEFT, padx=20)
        
        # 结果显示框架
        result_frame = ttk.LabelFrame(parent, text="回测结果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.result_text = scrolledtext.ScrolledText(result_frame, height=20, font=("Consolas", 10))
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
    def get_price_precision(self, price):
        """根据价格自动计算精度"""
        if price >= 1000:
            return 2
        elif price >= 1:
            return 4
        elif price >= 0.01:
            return 6
        else:
            return 8
    
    def on_ws_message(self, ws, message):
        """WebSocket消息处理"""
        try:
            data = json.loads(message)
            if 'c' in data:  # 最新价格
                self.current_price = float(data['c'])
        except Exception as e:
            print(f"WebSocket消息处理错误: {e}")
    
    def on_ws_error(self, ws, error):
        """WebSocket错误处理"""
        print(f"WebSocket错误: {error}")
    
    def on_ws_close(self, ws, close_status_code, close_msg):
        """WebSocket关闭处理"""
        print("WebSocket连接已关闭")
    
    def on_ws_open(self, ws):
        """WebSocket连接打开"""
        print("WebSocket连接已建立")
    
    def start_websocket(self, symbol):
        """启动WebSocket连接"""
        if self.ws:
            self.ws.close()
        
        # 使用代理
        ws_url = f"wss://fstream.binance.com/ws/{symbol.lower()}@ticker"
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=self.on_ws_message,
            on_error=self.on_ws_error,
            on_close=self.on_ws_close,
            on_open=self.on_ws_open
        )
        
        # 在新线程中运行WebSocket
        ws_thread = threading.Thread(target=lambda: self.ws.run_forever(
            http_proxy_host="127.0.0.1",
            http_proxy_port=7890,
            proxy_type="http"
        ), daemon=True)
        ws_thread.start()
    
    def get_klines(self, symbol, limit=60):
        """获取连续合约K线数据（1分钟）"""
        return self.get_klines_with_interval(symbol, "1m", limit)
    
    def get_klines_with_interval(self, symbol, interval, limit=60):
        """获取连续合约K线数据（指定周期）"""
        try:
            url = f"https://fapi.binance.com/fapi/v1/continuousKlines?pair={symbol}&contractType=PERPETUAL&interval={interval}&limit={limit}"
            proxies = {
                'http': 'http://127.0.0.1:7890',
                'https': 'http://127.0.0.1:7890'
            }
            response = requests.get(url, proxies=proxies, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"获取连续合约K线数据失败: {str(e)}")
    
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
                
                # 获取K线数据（每次更新）
                klines_data = self.get_klines(symbol)
                self.klines = deque(klines_data, maxlen=60)
                
                # 使用WebSocket获取的实时价格
                if self.current_price > 0:
                    price = self.current_price
                else:
                    # 如果WebSocket还没有数据，使用REST API
                    price = self.get_futures_price(symbol)
                
                # 根据价格自动调整精度
                self.price_precision = self.get_price_precision(price)
                
                current_time = datetime.now().strftime("%H:%M:%S")
                
                self.price_label.config(text=f"${price:.{self.price_precision}f}")
                self.info_label.config(text=f"{symbol} | 更新时间: {current_time} | WebSocket")
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
        
        # 保存配置
        symbol = self.symbol_entry.get().upper()
        self.config.set("monitor", "symbol", symbol)
            
        self.is_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.symbol_entry.config(state=tk.DISABLED)
        
        # 启动WebSocket连接
        self.start_websocket(symbol)
        
        # 在新线程中运行更新
        self.monitor_thread = threading.Thread(target=self.update_price, daemon=True)
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        
        # 关闭WebSocket连接
        if self.ws:
            self.ws.close()
            self.ws = None
        
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.symbol_entry.config(state=tk.NORMAL)
        self.status_label.config(text="已停止")
    
    def run_backtest(self):
        """运行回测"""
        try:
            # 获取参数
            symbol = self.bt_symbol_entry.get().upper()
            interval = self.interval_var.get()
            limit = int(self.bt_limit_entry.get())
            initial_capital = float(self.capital_entry.get())
            leverage = int(self.leverage_entry.get())
            full_position = self.full_position_var.get()
            long_strategy_name = self.long_strategy_var.get()
            close_long_strategy_name = self.close_long_strategy_var.get()
            short_strategy_name = self.short_strategy_var.get()
            close_short_strategy_name = self.close_short_strategy_var.get()
            
            # 保存配置
            self.config.set("backtest", "symbol", symbol)
            self.config.set("backtest", "interval", interval)
            self.config.set("backtest", "limit", limit)
            self.config.set("backtest", "initial_capital", initial_capital)
            self.config.set("backtest", "leverage", leverage)
            self.config.set("backtest", "full_position", full_position)
            self.config.set("backtest", "long_strategy", long_strategy_name)
            self.config.set("backtest", "close_long_strategy", close_long_strategy_name)
            self.config.set("backtest", "short_strategy", short_strategy_name)
            self.config.set("backtest", "close_short_strategy", close_short_strategy_name)
            
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "正在获取历史数据...\n")
            self.status_label.config(text="回测中...")
            self.backtest_btn.config(state=tk.DISABLED)
            
            # 在新线程中运行回测
            thread = threading.Thread(target=self._run_backtest_thread, 
                                     args=(symbol, interval, limit, initial_capital, leverage, full_position,
                                          long_strategy_name, close_long_strategy_name,
                                          short_strategy_name, close_short_strategy_name),
                                     daemon=True)
            thread.start()
            
        except Exception as e:
            messagebox.showerror("错误", f"回测参数错误: {str(e)}")
    
    def load_config_to_ui(self):
        """从配置加载到UI"""
        # 加载监控配置
        monitor_symbol = self.config.get("monitor", "symbol", "BTCUSDT")
        self.symbol_entry.insert(0, monitor_symbol)
        
        # 加载回测配置
        bt_symbol = self.config.get("backtest", "symbol", "BTCUSDT")
        self.bt_symbol_entry.insert(0, bt_symbol)
        
        interval = self.config.get("backtest", "interval", "1m")
        self.interval_var.set(interval)
        
        bt_limit = self.config.get("backtest", "limit", 500)
        self.bt_limit_entry.insert(0, str(bt_limit))
        
        initial_capital = self.config.get("backtest", "initial_capital", 10000)
        self.capital_entry.insert(0, str(initial_capital))
        
        leverage = self.config.get("backtest", "leverage", 5)
        self.leverage_entry.insert(0, str(leverage))
        
        full_position = self.config.get("backtest", "full_position", True)
        self.full_position_var.set(full_position)
        
        long_strategy = self.config.get("backtest", "long_strategy", list(STRATEGIES.keys())[0])
        self.long_strategy_var.set(long_strategy)
        
        close_long_strategy = self.config.get("backtest", "close_long_strategy", list(STRATEGIES.keys())[0])
        self.close_long_strategy_var.set(close_long_strategy)
        
        short_strategy = self.config.get("backtest", "short_strategy", list(STRATEGIES.keys())[0])
        self.short_strategy_var.set(short_strategy)
        
        close_short_strategy = self.config.get("backtest", "close_short_strategy", list(STRATEGIES.keys())[0])
        self.close_short_strategy_var.set(close_short_strategy)
    
    def _run_backtest_thread(self, symbol, interval, limit, initial_capital, leverage, full_position,
                            long_strategy_name, close_long_strategy_name,
                            short_strategy_name, close_short_strategy_name):
        """回测线程"""
        try:
            # 获取历史K线数据
            klines = self.get_klines_with_interval(symbol, interval, limit)
            
            self.result_text.insert(tk.END, f"获取到 {len(klines)} 根K线数据\n")
            self.result_text.insert(tk.END, f"K线周期: {interval}\n")
            self.result_text.insert(tk.END, f"杠杆倍数: {leverage}x\n")
            self.result_text.insert(tk.END, f"仓位模式: {'全仓' if full_position else '固定仓位'}\n")
            self.result_text.insert(tk.END, f"做多策略: {long_strategy_name}\n")
            self.result_text.insert(tk.END, f"平多策略: {close_long_strategy_name}\n")
            self.result_text.insert(tk.END, f"做空策略: {short_strategy_name}\n")
            self.result_text.insert(tk.END, f"平空策略: {close_short_strategy_name}\n")
            self.result_text.insert(tk.END, "=" * 60 + "\n\n")
            
            # 创建策略实例
            long_strategy = get_strategy(long_strategy_name)
            close_long_strategy = get_strategy(close_long_strategy_name)
            short_strategy = get_strategy(short_strategy_name)
            close_short_strategy = get_strategy(close_short_strategy_name)
            
            # 运行回测
            engine = BacktestEngine(initial_capital, leverage, full_position)
            result = engine.run(klines, long_strategy, close_long_strategy, 
                              short_strategy, close_short_strategy)
            
            # 显示结果
            self.result_text.insert(tk.END, "回测结果:\n")
            self.result_text.insert(tk.END, "-" * 60 + "\n")
            self.result_text.insert(tk.END, f"初始资金: ${result['initial_capital']:.2f}\n")
            self.result_text.insert(tk.END, f"最终资金: ${result['final_value']:.2f}\n")
            self.result_text.insert(tk.END, f"收益金额: ${result['profit']:.2f}\n")
            self.result_text.insert(tk.END, f"收益率: {result['profit_rate']:.2f}%\n")
            self.result_text.insert(tk.END, f"交易次数: {result['total_trades']}\n")
            self.result_text.insert(tk.END, f"杠杆倍数: {result['leverage']}x\n")
            self.result_text.insert(tk.END, f"仓位模式: {result['position_mode']}\n")
            self.result_text.insert(tk.END, "\n" + "=" * 60 + "\n\n")
            
            # 显示交易记录
            if result['trades']:
                self.result_text.insert(tk.END, "交易记录:\n")
                self.result_text.insert(tk.END, "-" * 60 + "\n")
                
                # 获取价格精度
                avg_price = sum(t['price'] for t in result['trades']) / len(result['trades'])
                precision = self.get_price_precision(avg_price)
                
                for i, trade in enumerate(result['trades'], 1):
                    time_str = trade['time'].strftime("%Y-%m-%d %H:%M:%S")
                    trade_type = trade['type']
                    
                    if 'profit' in trade:
                        # 平仓或爆仓记录
                        self.result_text.insert(tk.END, 
                            f"{i}. [{time_str}] {trade_type} - "
                            f"价格: ${trade['price']:.{precision}f}, "
                            f"数量: {trade['amount']:.6f}, "
                            f"盈亏: ${trade['profit']:.2f}, "
                            f"资金: ${trade['capital']:.2f}\n")
                    else:
                        # 开仓记录
                        self.result_text.insert(tk.END, 
                            f"{i}. [{time_str}] {trade_type} - "
                            f"价格: ${trade['price']:.{precision}f}, "
                            f"数量: {trade['amount']:.6f}, "
                            f"保证金: ${trade['margin']:.2f}, "
                            f"杠杆: {trade['leverage']}x, "
                            f"资金: ${trade['capital']:.2f}\n")
            else:
                self.result_text.insert(tk.END, "无交易记录\n")
            
            self.status_label.config(text="回测完成")
            
        except Exception as e:
            self.result_text.insert(tk.END, f"\n错误: {str(e)}\n")
            self.status_label.config(text=f"回测失败: {str(e)}")
        finally:
            self.backtest_btn.config(state=tk.NORMAL)


def main():
    root = tk.Tk()
    app = BinanceMonitor(root)
    root.mainloop()


if __name__ == "__main__":
    main()

