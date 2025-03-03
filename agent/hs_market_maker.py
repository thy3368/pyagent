import os
import json
import time
import logging
import random
from decimal import Decimal
from typing import Dict, List, Tuple, Any
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/Users/hongyaotang/src/py/pyagent/logs/hs_market_maker.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("HS_MarketMaker")

class HSMarketMaker:
    """恒生电子做市商模拟"""
    
    # 恒生电子股票代码
    STOCK_CODE = "600570.SH"
    
    def __init__(self):
        """初始化做市商"""
        # 设置初始参数
        self.stock_code = self.STOCK_CODE
        self.stock_name = "恒生电子"
        
        # 做市参数
        self.spread = Decimal("0.02")  # 买卖价差2%
        self.position_limit = 10000    # 最大持仓数量
        self.tick_size = Decimal("0.01")  # 最小价格变动
        self.lot_size = 100  # 最小交易单位
        self.risk_limit = Decimal("0.05")  # 风险限制，价格变动超过5%时调整策略
        
        # 市场状态
        self.last_price = Decimal("55.00")  # 初始价格
        self.position = 0  # 当前持仓
        self.cash = Decimal("5000000.00")  # 初始资金
        self.nav = self.cash  # 净资产价值
        
        # 交易记录
        self.trades = []
        self.quotes = []
        
        # 市场数据
        self.market_data = self._generate_historical_data()
        
        logger.info(f"初始化恒生电子({self.stock_code})做市商，初始价格: {self.last_price}，初始资金: {self.cash}")
    
    def _generate_historical_data(self) -> pd.DataFrame:
        """生成模拟历史数据
        
        Returns:
            历史价格数据
        """
        # 生成过去30天的数据
        dates = []
        prices = []
        volumes = []
        
        base_price = 55.00
        current_price = base_price
        
        for i in range(30):
            date = (datetime.now() - timedelta(days=30-i)).strftime("%Y-%m-%d")
            dates.append(date)
            
            # 生成随机价格波动
            price_change = random.uniform(-1.0, 1.0)
            current_price = max(current_price + price_change, 40.0)  # 确保价格不低于40
            prices.append(round(current_price, 2))
            
            # 生成随机成交量
            volume = random.randint(500000, 2000000)
            volumes.append(volume)
        
        # 创建DataFrame
        df = pd.DataFrame({
            "date": dates,
            "price": prices,
            "volume": volumes
        })
        
        return df
    
    def calculate_quotes(self) -> Tuple[Decimal, Decimal]:
        """计算买卖报价
        
        Returns:
            (买入价, 卖出价)
        """
        mid_price = self.last_price
        half_spread = mid_price * self.spread / 2
        
        # 基础报价
        bid_price = mid_price - half_spread
        ask_price = mid_price + half_spread
        
        # 根据持仓调整报价
        position_factor = Decimal(self.position) / Decimal(self.position_limit) * Decimal("0.01")
        bid_price -= position_factor * mid_price
        ask_price -= position_factor * mid_price
        
        # 确保价格符合最小变动单位
        bid_price = (bid_price / self.tick_size).quantize(Decimal("1")) * self.tick_size
        ask_price = (ask_price / self.tick_size).quantize(Decimal("1")) * self.tick_size
        
        # 记录报价
        self.quotes.append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "bid_price": float(bid_price),
            "ask_price": float(ask_price),
            "mid_price": float(mid_price),
            "position": self.position,
            "nav": float(self.nav)
        })
        
        return bid_price, ask_price
    
    def execute_trade(self, side: str, price: Decimal, quantity: int) -> Dict[str, Any]:
        """执行交易
        
        Args:
            side: 交易方向 ("buy" 或 "sell")
            price: 成交价格
            quantity: 成交数量
            
        Returns:
            交易结果
        """
        # 确保数量为手数的整数倍
        quantity = (quantity // self.lot_size) * self.lot_size
        if quantity <= 0:
            return {"success": False, "error": "交易数量必须大于0"}
        
        # 计算交易金额
        amount = price * Decimal(quantity)
        
        # 计算交易费用 (假设佣金为0.1%)
        commission = amount * Decimal("0.001")
        
        # 执行交易
        if side == "buy":
            # 检查资金是否足够
            if amount + commission > self.cash:
                return {"success": False, "error": "资金不足"}
                
            # 更新持仓和资金
            self.position += quantity
            self.cash -= amount + commission
        else:  # sell
            # 检查持仓是否足够
            if quantity > self.position:
                return {"success": False, "error": "持仓不足"}
                
            # 更新持仓和资金
            self.position -= quantity
            self.cash += amount - commission
        
        # 更新最新价格
        self.last_price = price
        
        # 更新净资产价值
        self.nav = self.cash + Decimal(self.position) * self.last_price
        
        # 记录交易
        trade = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "side": side,
            "price": float(price),
            "quantity": quantity,
            "amount": float(amount),
            "commission": float(commission),
            "position": self.position,
            "cash": float(self.cash),
            "nav": float(self.nav)
        }
        self.trades.append(trade)
        
        logger.info(f"执行交易: {side} {quantity}股 @ {price}，持仓: {self.position}，资金: {self.cash}")
        
        return {
            "success": True,
            "trade": trade
        }
    
    def simulate_market_activity(self) -> Dict[str, Any]:
        """模拟市场活动，生成随机订单
        
        Returns:
            市场活动结果
        """
        # 计算当前报价
        bid_price, ask_price = self.calculate_quotes()
        
        # 随机决定是否有市场订单
        if random.random() < 0.7:  # 70%的概率有市场订单
            # 随机决定订单方向
            if random.random() < 0.5:  # 50%的概率是买单
                # 市场买单，我们卖出
                price = bid_price
                max_quantity = self.position  # 最多卖出当前持仓
                if max_quantity > 0:
                    quantity = random.randint(1, min(max_quantity, 1000))
                    return self.execute_trade("sell", price, quantity)
            else:  # 50%的概率是卖单
                # 市场卖单，我们买入
                price = ask_price
                max_quantity = int(self.cash / price / 1.001)  # 考虑佣金
                max_quantity = min(max_quantity, self.position_limit - self.position)  # 考虑持仓限制
                if max_quantity > 0:
                    quantity = random.randint(1, min(max_quantity, 1000))
                    return self.execute_trade("buy", price, quantity)
        
        # 如果没有交易发生
        return {"success": False, "reason": "无市场订单"}
    
    def update_market_price(self) -> None:
        """更新市场价格"""
        # 生成随机价格变动
        price_change_pct = random.uniform(-0.01, 0.01)  # 随机±1%的价格变动
        price_change = self.last_price * Decimal(str(price_change_pct))
        
        # 更新价格
        new_price = self.last_price + price_change
        
        # 确保价格为最小变动单位的整数倍
        new_price = (new_price / self.tick_size).quantize(Decimal("1")) * self.tick_size
        
        # 更新最新价格
        self.last_price = new_price
        
        # 更新净资产价值
        self.nav = self.cash + Decimal(self.position) * self.last_price
        
        logger.info(f"市场价格更新: {self.last_price}，持仓价值: {Decimal(self.position) * self.last_price}，净资产: {self.nav}")
    
    def run_simulation(self, days: int = 1, trades_per_day: int = 100) -> None:
        """运行模拟交易
        
        Args:
            days: 模拟天数
            trades_per_day: 每天交易次数
        """
        logger.info(f"开始模拟交易: {days}天, 每天{trades_per_day}次交易")
        
        total_trades = days * trades_per_day
        successful_trades = 0
        
        for i in range(total_trades):
            # 更新市场价格
            if i % 10 == 0:  # 每10次交易更新一次价格
                self.update_market_price()
            
            # 模拟市场活动
            result = self.simulate_market_activity()
            if result.get("success", False):
                successful_trades += 1
            
            # 模拟时间流逝
            time.sleep(0.01)
        
        logger.info(f"模拟交易结束: 总共{total_trades}次尝试, {successful_trades}次成功交易")
        logger.info(f"最终状态: 持仓={self.position}, 资金={self.cash}, 净资产={self.nav}")
        
        # 保存交易记录
        self.save_results()
        
        # 绘制图表
        self.plot_results()
    
    def save_results(self) -> None:
        """保存交易结果"""
        output_dir = "/Users/hongyaotang/src/py/pyagent/output"
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存交易记录
        if self.trades:
            trades_df = pd.DataFrame(self.trades)
            trades_path = f"{output_dir}/hs_trades_{int(time.time())}.csv"
            trades_df.to_csv(trades_path, index=False)
            logger.info(f"交易记录已保存到: {trades_path}")
        
        # 保存报价记录
        if self.quotes:
            quotes_df = pd.DataFrame(self.quotes)
            quotes_path = f"{output_dir}/hs_quotes_{int(time.time())}.csv"
            quotes_df.to_csv(quotes_path, index=False)
            logger.info(f"报价记录已保存到: {quotes_path}")
    
    def plot_results(self) -> None:
        """绘制交易结果图表"""
        if not self.trades:
            logger.warning("没有交易记录，无法绘制图表")
            return
        
        # 创建交易DataFrame
        trades_df = pd.DataFrame(self.trades)
        trades_df["timestamp"] = pd.to_datetime(trades_df["timestamp"])
        
        # 创建报价DataFrame
        quotes_df = pd.DataFrame(self.quotes)
        quotes_df["timestamp"] = pd.to_datetime(quotes_df["timestamp"])
        
        # 绘制价格和净资产图表
        plt.figure(figsize=(12, 8))
        
        # 绘制子图1: 价格和交易
        plt.subplot(2, 1, 1)
        plt.plot(quotes_df["timestamp"], quotes_df["bid_price"], 'b-', label="买入价", alpha=0.5)
        plt.plot(quotes_df["timestamp"], quotes_df["ask_price"], 'r-', label="卖出价", alpha=0.5)
        plt.plot(quotes_df["timestamp"], quotes_df["mid_price"], 'g-', label="中间价", alpha=0.7)
        
        # 绘制买入和卖出点
        buy_trades = trades_df[trades_df["side"] == "buy"]
        sell_trades = trades_df[trades_df["side"] == "sell"]
        
        if not buy_trades.empty:
            plt.scatter(buy_trades["timestamp"], buy_trades["price"], color="green", label="买入", marker="^", s=100)
        
        if not sell_trades.empty:
            plt.scatter(sell_trades["timestamp"], sell_trades["price"], color="red", label="卖出", marker="v", s=100)
        
        plt.title("恒生电子做市商 - 价格和交易")
        plt.xlabel("时间")
        plt.ylabel("价格 (元)")
        plt.legend()
        plt.grid(True)
        
        # 绘制子图2: 净资产和持仓
        plt.subplot(2, 1, 2)
        plt.plot(quotes_df["timestamp"], quotes_df["nav"], 'b-', label="净资产")
        
        # 创建第二个Y轴
        ax2 = plt.twinx()
        ax2.plot(quotes_df["timestamp"], quotes_df["position"], 'r-', label="持仓")
        
        plt.title("恒生电子做市商 - 净资产和持仓")
        plt.xlabel("时间")
        plt.ylabel("净资产 (元)")
        ax2.set_ylabel("持仓 (股)")
        
        # 合并两个图例
        lines1, labels1 = plt.gca().get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
        
        plt.grid(True)
        
        # 调整布局
        plt.tight_layout()
        
        # 保存图表
        output_dir = "/Users/hongyaotang/src/py/pyagent/output"
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = f"{output_dir}/hs_market_maker_{int(time.time())}.png"
        plt.savefig(output_path)
        logger.info(f"交易图表已保存到: {output_path}")
        
        # 关闭图表
        plt.close()

def main():
    """主函数"""
    # 创建做市商
    market_maker = HSMarketMaker()
    
    # 运行模拟
    market_maker.run_simulation(days=1, trades_per_day=100)

if __name__ == "__main__":
    main()