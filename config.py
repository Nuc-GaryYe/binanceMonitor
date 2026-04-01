#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
"""

import json
import os


class Config:
    """配置管理类"""
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.load()
    
    def load(self):
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置失败: {e}")
                return self.get_default_config()
        return self.get_default_config()
    
    def save(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def get_default_config(self):
        """获取默认配置"""
        return {
            "monitor": {
                "symbol": "BTCUSDT"
            },
            "backtest": {
                "symbol": "BTCUSDT",
                "limit": 500,
                "initial_capital": 10000,
                "leverage": 5,
                "full_position": True,
                "long_strategy": "MA5/60交叉",
                "close_long_strategy": "MA5/60交叉",
                "short_strategy": "MA5/60交叉",
                "close_short_strategy": "MA5/60交叉"
            }
        }
    
    def get(self, section, key, default=None):
        """获取配置项"""
        return self.config.get(section, {}).get(key, default)
    
    def set(self, section, key, value):
        """设置配置项"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self.save()
