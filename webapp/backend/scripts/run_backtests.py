#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.backtest_runner import run_backtest
from backtest.strategies import SmaCrossover, RSIStrategy, MACDStrategy

# Run a few standard strategies
run_backtest(SmaCrossover, {'fast': 10, 'slow': 30, 'position_size': 0.95})
run_backtest(RSIStrategy, {'period': 14, 'oversold': 30, 'overbought': 70, 'position_size': 0.2})
run_backtest(MACDStrategy, {'fast': 12, 'slow': 26, 'signal': 9, 'position_size': 0.9})