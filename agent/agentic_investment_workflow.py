import os
import json
import time
import logging
from typing import Dict, List, Any
from decimal import Decimal
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from dataclasses import dataclass
from enum import Enum

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/Users/hongyaotang/src/py/pyagent/logs/agentic_investment.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Agentic_Investment")

class MarketTrend(Enum):
    BULLISH = "上涨"
    BEARISH = "下跌"
    NEUTRAL = "震荡"

@dataclass
class MarketState:
    """市场状态"""
    trend: MarketTrend
    volatility: float
    sentiment: float
    risk_level: int  # 1-10，风险等级

@dataclass
class InvestmentStrategy:
    """投资策略"""
    position_size: float  # 仓位比例
    stop_loss: float     # 止损比例
    take_profit: float   # 止盈比例
    risk_tolerance: int  # 1-10，风险承受能力

class AgentRole:
    """Agent角色基类"""
    def __init__(self, name: str):
        self.name = name
        self.memory: List[Dict] = []
    
    def remember(self, event: Dict):
        """记录事件"""
        event["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.memory.append(event)
    
    def recall(self, n: int = 5) -> List[Dict]:
        """回忆最近的n个事件"""
        return self.memory[-n:]

class MarketAnalyst(AgentRole):
    """市场分析师角色"""
    def __init__(self):
        super().__init__("Market_Analyst")
    
    def analyze_market(self, data: pd.DataFrame) -> MarketState:
        """分析市场状态"""
        # 计算趋势
        price_change = (data["close"].iloc[-1] / data["close"].iloc[0] - 1) * 100
        if price_change > 2:
            trend = MarketTrend.BULLISH
        elif price_change < -2:
            trend = MarketTrend.BEARISH
        else:
            trend = MarketTrend.NEUTRAL
        
        # 计算波动率
        volatility = data["close"].pct_change().std() * 100
        
        # 模拟市场情绪（基于成交量和价格变化）
        volume_change = data["volume"].pct_change().mean()
        sentiment = (volume_change + price_change/100) / 2
        
        # 评估风险等级
        risk_level = min(10, max(1, int((volatility * 2 + abs(sentiment) * 5))))
        
        market_state = MarketState(
            trend=trend,
            volatility=volatility,
            sentiment=sentiment,
            risk_level=risk_level
        )
        
        self.remember({
            "action": "market_analysis",
            "result": {
                "trend": trend.value,
                "volatility": f"{volatility:.2f}%",
                "sentiment": f"{sentiment:.2f}",
                "risk_level": risk_level
            }
        })
        
        return market_state

class StrategyAdvisor(AgentRole):
    """策略顾问角色"""
    def __init__(self):
        super().__init__("Strategy_Advisor")
    
    def generate_strategy(self, market_state: MarketState, risk_preference: int) -> InvestmentStrategy:
        """生成投资策略"""
        # 基于市场状态和风险偏好生成策略
        
        # 计算仓位
        base_position = 0.5  # 基础仓位50%
        trend_factor = {
            MarketTrend.BULLISH: 0.2,
            MarketTrend.BEARISH: -0.2,
            MarketTrend.NEUTRAL: 0
        }[market_state.trend]
        
        risk_factor = (risk_preference - market_state.risk_level) / 20  # -0.45 到 0.45
        position_size = max(0.1, min(0.9, base_position + trend_factor + risk_factor))
        
        # 设置止损止盈
        stop_loss = 0.05 + (10 - risk_preference) * 0.01  # 5%-15%
        take_profit = 0.10 + risk_preference * 0.02  # 10%-30%
        
        strategy = InvestmentStrategy(
            position_size=position_size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_tolerance=risk_preference
        )
        
        self.remember({
            "action": "strategy_generation",
            "result": {
                "position_size": f"{position_size:.2%}",
                "stop_loss": f"{stop_loss:.2%}",
                "take_profit": f"{take_profit:.2%}",
                "risk_tolerance": risk_preference
            }
        })
        
        return strategy

class TradeExecutor(AgentRole):
    """交易执行者角色"""
    def __init__(self):
        super().__init__("Trade_Executor")
        self.portfolio = {
            "cash": 1000000.0,
            "positions": {}
        }
    
    def execute_trade(self, symbol: str, strategy: InvestmentStrategy, current_price: float) -> Dict[str, Any]:
        """执行交易"""
        available_cash = self.portfolio["cash"]
        current_position = self.portfolio["positions"].get(symbol, 0)
        
        # 计算目标仓位金额
        target_position_value = (available_cash + current_position * current_price) * strategy.position_size
        target_position_size = int(target_position_value / current_price)
        
        # 计算需要交易的数量
        trade_size = target_position_size - current_position
        
        if trade_size == 0:
            return {"success": True, "action": "hold", "reason": "目标仓位无需调整"}
        
        action = "buy" if trade_size > 0 else "sell"
        trade_value = abs(trade_size) * current_price
        commission = trade_value * 0.001  # 0.1%手续费
        
        # 检查资金是否足够
        if action == "buy" and trade_value + commission > available_cash:
            return {"success": False, "action": action, "reason": "资金不足"}
        
        # 执行交易
        if action == "buy":
            self.portfolio["cash"] -= (trade_value + commission)
            self.portfolio["positions"][symbol] = current_position + trade_size
        else:
            self.portfolio["cash"] += (trade_value - commission)
            self.portfolio["positions"][symbol] = current_position + trade_size
        
        trade_result = {
            "success": True,
            "action": action,
            "symbol": symbol,
            "size": abs(trade_size),
            "price": current_price,
            "value": trade_value,
            "commission": commission,
            "portfolio": {
                "cash": self.portfolio["cash"],
                "positions": self.portfolio["positions"]
            }
        }
        
        self.remember({
            "action": "trade_execution",
            "result": trade_result
        })
        
        return trade_result

class InvestmentWorkflow:
    """投资工作流"""
    def __init__(self):
        self.analyst = MarketAnalyst()
        self.advisor = StrategyAdvisor()
        self.executor = TradeExecutor()
        self.history = []
    
    def _generate_mock_data(self) -> pd.DataFrame:
        """生成模拟市场数据"""
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        np.random.seed(42)
        
        # 生成价格数据
        prices = np.random.normal(loc=100, scale=2, size=30).cumsum()
        prices = np.maximum(prices, 50)  # 确保价格为正
        
        # 生成成交量数据
        volumes = np.random.normal(loc=1000000, scale=200000, size=30)
        volumes = np.maximum(volumes, 100000)  # 确保成交量为正
        
        return pd.DataFrame({
            'date': dates,
            'close': prices,
            'volume': volumes
        })
    
    def run(self, symbol: str, risk_preference: int = 5) -> Dict[str, Any]:
        """运行投资工作流
        
        Args:
            symbol: 交易标的
            risk_preference: 风险偏好(1-10)
            
        Returns:
            工作流执行结果
        """
        logger.info(f"开始执行投资工作流: {symbol}, 风险偏好: {risk_preference}")
        
        # 获取市场数据
        market_data = self._generate_mock_data()
        current_price = float(market_data["close"].iloc[-1])
        
        # 1. 市场分析
        logger.info("执行市场分析...")
        market_state = self.analyst.analyze_market(market_data)
        logger.info(f"市场状态: 趋势={market_state.trend.value}, "
                   f"波动率={market_state.volatility:.2f}%, "
                   f"情绪={market_state.sentiment:.2f}, "
                   f"风险等级={market_state.risk_level}")
        
        # 2. 生成策略
        logger.info("生成投资策略...")
        strategy = self.advisor.generate_strategy(market_state, risk_preference)
        logger.info(f"投资策略: 仓位={strategy.position_size:.2%}, "
                   f"止损={strategy.stop_loss:.2%}, "
                   f"止盈={strategy.take_profit:.2%}")
        
        # 3. 执行交易
        logger.info("执行交易...")
        trade_result = self.executor.execute_trade(symbol, strategy, current_price)
        logger.info(f"交易结果: {trade_result}")
        
        # 记录工作流结果
        workflow_result = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": symbol,
            "risk_preference": risk_preference,
            "market_state": {
                "trend": market_state.trend.value,
                "volatility": f"{market_state.volatility:.2f}%",
                "sentiment": f"{market_state.sentiment:.2f}",
                "risk_level": market_state.risk_level
            },
            "strategy": {
                "position_size": f"{strategy.position_size:.2%}",
                "stop_loss": f"{strategy.stop_loss:.2%}",
                "take_profit": f"{strategy.take_profit:.2%}"
            },
            "trade_result": trade_result
        }
        
        self.history.append(workflow_result)
        
        return workflow_result
    
    def save_results(self) -> None:
        """保存工作流结果"""
        if not self.history:
            return
            
        output_dir = "/Users/hongyaotang/src/py/pyagent/output"
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存为JSON文件
        output_path = f"{output_dir}/investment_workflow_{int(time.time())}.json"
        with open(output_path, 'w') as f:
            json.dump(self.history, f, indent=2)
        
        logger.info(f"工作流结果已保存到: {output_path}")

def main():
    """主函数"""
    # 创建工作流实例
    workflow = InvestmentWorkflow()
    
    # 模拟运行多次工作流
    symbols = ["AAPL", "GOOGL", "MSFT"]
    risk_preferences = [3, 5, 7]  # 不同的风险偏好
    
    for symbol in symbols:
        for risk_pref in risk_preferences:
            result = workflow.run(symbol, risk_pref)
            time.sleep(1)  # 模拟时间间隔
    
    # 保存结果
    workflow.save_results()

if __name__ == "__main__":
    main()