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
        logging.FileHandler("/Users/hongyaotang/src/py/pyagent/logs/hs_market_value_manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("HS_MarketValueManager")

class HSMarketValueManager:
    """恒生电子市值管理模拟"""
    
    # 恒生电子股票代码
    STOCK_CODE = "600570.SH"
    
    def __init__(self):
        """初始化市值管理器"""
        # 设置初始参数
        self.stock_code = self.STOCK_CODE
        self.stock_name = "恒生电子"
        
        # 公司基本信息
        self.total_shares = 1000000000  # 总股本(股)
        self.float_shares = 800000000   # 流通股本(股)
        self.stock_price = Decimal("55.00")  # 当前股价
        self.market_value = self.total_shares * self.stock_price  # 总市值
        self.float_market_value = self.float_shares * self.stock_price  # 流通市值
        
        # 财务数据
        self.cash_reserve = Decimal("5000000000.00")  # 现金储备(元)
        self.annual_profit = Decimal("2000000000.00")  # 年度利润(元)
        self.eps = self.annual_profit / Decimal(self.total_shares)  # 每股收益
        self.pe_ratio = self.stock_price / self.eps  # 市盈率
        
        # 回购参数
        self.max_buyback_ratio = Decimal("0.10")  # 最大回购比例(占流通股本)
        self.max_buyback_price = Decimal("65.00")  # 最高回购价格
        self.min_buyback_price = Decimal("45.00")  # 最低回购价格
        self.buyback_budget = Decimal("500000000.00")  # 回购预算
        
        # 分红参数
        self.dividend_payout_ratio = Decimal("0.30")  # 分红比例(占年度利润)
        
        # 市场数据
        self.market_data = self._generate_historical_data()
        
        # 操作记录
        self.operations = []
        self.price_history = []
        
        logger.info(f"初始化恒生电子({self.stock_code})市值管理器")
        logger.info(f"初始总股本: {self.total_shares}股, 流通股本: {self.float_shares}股")
        logger.info(f"初始股价: {self.stock_price}元, 总市值: {self.market_value/100000000:.2f}亿元")
        logger.info(f"现金储备: {self.cash_reserve/100000000:.2f}亿元, 年度利润: {self.annual_profit/100000000:.2f}亿元")
    
    def _generate_historical_data(self) -> pd.DataFrame:
        """生成模拟历史数据
        
        Returns:
            历史价格数据
        """
        # 生成过去365天的数据
        dates = []
        prices = []
        volumes = []
        
        base_price = 55.00
        current_price = base_price
        
        for i in range(365):
            date = (datetime.now() - timedelta(days=365-i)).strftime("%Y-%m-%d")
            dates.append(date)
            
            # 生成随机价格波动
            price_change = random.uniform(-1.0, 1.0)
            current_price = max(current_price + price_change, 40.0)  # 确保价格不低于40
            prices.append(round(current_price, 2))
            
            # 生成随机成交量
            volume = random.randint(5000000, 20000000)
            volumes.append(volume)
        
        # 创建DataFrame
        df = pd.DataFrame({
            "date": dates,
            "price": prices,
            "volume": volumes
        })
        
        return df
    
    def update_market_price(self, days: int = 1) -> None:
        """更新市场价格
        
        Args:
            days: 模拟天数
        """
        for _ in range(days):
            # 生成随机价格变动
            price_change_pct = random.uniform(-0.03, 0.03)  # 随机±3%的价格变动
            price_change = self.stock_price * Decimal(str(price_change_pct))
            
            # 更新价格
            new_price = self.stock_price + price_change
            new_price = max(new_price, Decimal("40.00"))  # 确保价格不低于40元
            
            # 更新股价
            self.stock_price = new_price.quantize(Decimal("0.01"))
            
            # 更新市值
            self.market_value = self.total_shares * self.stock_price
            self.float_market_value = self.float_shares * self.stock_price
            
            # 更新市盈率
            self.pe_ratio = self.stock_price / self.eps
            
            # 记录价格历史
            self.price_history.append({
                "date": datetime.now().strftime("%Y-%m-%d"),
                "price": float(self.stock_price),
                "market_value": float(self.market_value),
                "pe_ratio": float(self.pe_ratio)
            })
            
            logger.info(f"市场价格更新: {self.stock_price}元, 总市值: {self.market_value/100000000:.2f}亿元, 市盈率: {self.pe_ratio:.2f}")
    
    def execute_stock_buyback(self, amount: Decimal = None) -> Dict[str, Any]:
        """执行股票回购
        
        Args:
            amount: 回购金额，默认为回购预算的10%
            
        Returns:
            回购结果
        """
        if amount is None:
            amount = self.buyback_budget * Decimal("0.1")
        
        # 检查回购价格是否在合理范围内
        if self.stock_price > self.max_buyback_price:
            logger.info(f"当前股价({self.stock_price})高于最高回购价格({self.max_buyback_price})，暂不回购")
            return {"success": False, "reason": "股价过高"}
        
        if self.stock_price < self.min_buyback_price:
            logger.info(f"当前股价({self.stock_price})低于最低回购价格({self.min_buyback_price})，暂不回购")
            return {"success": False, "reason": "股价过低"}
        
        # 检查现金储备是否足够
        if amount > self.cash_reserve * Decimal("0.2"):  # 不使用超过现金储备20%的资金
            amount = self.cash_reserve * Decimal("0.2")
            logger.info(f"调整回购金额至现金储备的20%: {amount}元")
        
        # 计算回购股数
        buyback_shares = int(amount / self.stock_price)
        
        # 检查回购股数是否超过限制
        max_buyback_shares = int(self.float_shares * self.max_buyback_ratio)
        if buyback_shares > max_buyback_shares:
            buyback_shares = max_buyback_shares
            amount = Decimal(buyback_shares) * self.stock_price
            logger.info(f"调整回购股数至流通股本的{self.max_buyback_ratio*100}%: {buyback_shares}股")
        
        # 执行回购
        self.cash_reserve -= amount
        self.float_shares -= buyback_shares
        self.total_shares -= buyback_shares  # 假设回购后注销
        
        # 更新每股收益
        self.eps = self.annual_profit / Decimal(self.total_shares)
        
        # 更新市值
        self.market_value = self.total_shares * self.stock_price
        self.float_market_value = self.float_shares * self.stock_price
        
        # 记录操作
        operation = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "type": "buyback",
            "shares": buyback_shares,
            "price": float(self.stock_price),
            "amount": float(amount),
            "total_shares_after": self.total_shares,
            "float_shares_after": self.float_shares,
            "cash_reserve_after": float(self.cash_reserve)
        }
        self.operations.append(operation)
        
        logger.info(f"执行股票回购: {buyback_shares}股 @ {self.stock_price}元, 总金额: {amount}元")
        logger.info(f"回购后总股本: {self.total_shares}股, 流通股本: {self.float_shares}股")
        logger.info(f"回购后现金储备: {self.cash_reserve}元, 每股收益: {self.eps}元")
        
        # 回购可能会影响股价
        price_impact = random.uniform(0.005, 0.02)  # 0.5%~2%的正面影响
        self.stock_price = self.stock_price * (1 + Decimal(str(price_impact)))
        logger.info(f"回购对股价的影响: +{price_impact*100:.2f}%, 新股价: {self.stock_price}元")
        
        return {
            "success": True,
            "shares": buyback_shares,
            "amount": float(amount),
            "price": float(self.stock_price)
        }
    
    def execute_dividend_payment(self, payout_ratio: Decimal = None) -> Dict[str, Any]:
        """执行股息发放
        
        Args:
            payout_ratio: 分红比例，默认为设定的分红比例
            
        Returns:
            分红结果
        """
        if payout_ratio is None:
            payout_ratio = self.dividend_payout_ratio
        
        # 计算分红总额
        dividend_amount = self.annual_profit * payout_ratio
        
        # 检查现金储备是否足够
        if dividend_amount > self.cash_reserve * Decimal("0.3"):  # 不使用超过现金储备30%的资金
            payout_ratio = self.cash_reserve * Decimal("0.3") / self.annual_profit
            dividend_amount = self.annual_profit * payout_ratio
            logger.info(f"调整分红比例至{payout_ratio*100:.2f}%, 分红总额: {dividend_amount}元")
        
        # 计算每股股息
        dividend_per_share = dividend_amount / Decimal(self.total_shares)
        
        # 执行分红
        self.cash_reserve -= dividend_amount
        
        # 记录操作
        operation = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "type": "dividend",
            "payout_ratio": float(payout_ratio),
            "total_amount": float(dividend_amount),
            "per_share": float(dividend_per_share),
            "cash_reserve_after": float(self.cash_reserve)
        }
        self.operations.append(operation)
        
        logger.info(f"执行股息发放: 分红比例{payout_ratio*100:.2f}%, 总金额: {dividend_amount}元")
        logger.info(f"每股股息: {dividend_per_share}元, 分红后现金储备: {self.cash_reserve}元")
        
        # 分红可能会影响股价
        price_impact = random.uniform(-0.01, 0.02)  # -1%~2%的影响
        self.stock_price = self.stock_price * (1 + Decimal(str(price_impact)))
        logger.info(f"分红对股价的影响: {price_impact*100:+.2f}%, 新股价: {self.stock_price}元")
        
        return {
            "success": True,
            "payout_ratio": float(payout_ratio),
            "total_amount": float(dividend_amount),
            "per_share": float(dividend_per_share)
        }
    
    def execute_stock_split(self, ratio: int = 2) -> Dict[str, Any]:
        """执行股票拆分
        
        Args:
            ratio: 拆分比例，如2表示1拆2
            
        Returns:
            拆分结果
        """
        # 更新股本
        self.total_shares *= ratio
        self.float_shares *= ratio
        
        # 更新股价
        self.stock_price = self.stock_price / Decimal(ratio)
        
        # 更新每股收益
        self.eps = self.annual_profit / Decimal(self.total_shares)
        
        # 记录操作
        operation = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "type": "split",
            "ratio": ratio,
            "total_shares_after": self.total_shares,
            "float_shares_after": self.float_shares,
            "price_after": float(self.stock_price),
            "eps_after": float(self.eps)
        }
        self.operations.append(operation)
        
        logger.info(f"执行股票拆分: 1拆{ratio}")
        logger.info(f"拆分后总股本: {self.total_shares}股, 流通股本: {self.float_shares}股")
        logger.info(f"拆分后股价: {self.stock_price}元, 每股收益: {self.eps}元")
        
        # 拆分可能会影响股价
        price_impact = random.uniform(0.01, 0.05)  # 1%~5%的正面影响
        self.stock_price = self.stock_price * (1 + Decimal(str(price_impact)))
        logger.info(f"拆分对股价的影响: +{price_impact*100:.2f}%, 新股价: {self.stock_price}元")
        
        return {
            "success": True,
            "ratio": ratio,
            "price_before": float(self.stock_price / (1 + Decimal(str(price_impact)))),
            "price_after": float(self.stock_price)
        }
    
    def execute_equity_incentive(self, shares: int, price_discount: Decimal = Decimal("0.8")) -> Dict[str, Any]:
        """执行股权激励
        
        Args:
            shares: 激励股份数量
            price_discount: 价格折扣，如0.8表示以市价的80%授予
            
        Returns:
            激励结果
        """
        # 计算激励股份价值
        incentive_price = self.stock_price * price_discount
        incentive_value = Decimal(shares) * incentive_price
        
        # 更新股本
        self.total_shares += shares
        self.float_shares += shares  # 假设激励股份全部流通
        
        # 更新每股收益
        self.eps = self.annual_profit / Decimal(self.total_shares)
        
        # 记录操作
        operation = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "type": "equity_incentive",
            "shares": shares,
            "price": float(incentive_price),
            "value": float(incentive_value),
            "total_shares_after": self.total_shares,
            "float_shares_after": self.float_shares,
            "eps_after": float(self.eps)
        }
        self.operations.append(operation)
        
        logger.info(f"执行股权激励: {shares}股 @ {incentive_price}元, 总价值: {incentive_value}元")
        logger.info(f"激励后总股本: {self.total_shares}股, 流通股本: {self.float_shares}股")
        logger.info(f"激励后每股收益: {self.eps}元")
        
        # 股权激励可能会影响股价
        price_impact = random.uniform(-0.02, 0.03)  # -2%~3%的影响
        self.stock_price = self.stock_price * (1 + Decimal(str(price_impact)))
        logger.info(f"股权激励对股价的影响: {price_impact*100:+.2f}%, 新股价: {self.stock_price}元")
        
        return {
            "success": True,
            "shares": shares,
            "price": float(incentive_price),
            "value": float(incentive_value)
        }
    
    def execute_private_placement(self, amount: Decimal, price_discount: Decimal = Decimal("0.9")) -> Dict[str, Any]:
        """执行定向增发
        
        Args:
            amount: 募集资金金额
            price_discount: 价格折扣，如0.9表示以市价的90%发行
            
        Returns:
            增发结果
        """
        # 计算发行价格和股数
        issue_price = self.stock_price * price_discount
        issue_shares = int(amount / issue_price)
        
        # 更新股本和现金储备
        self.total_shares += issue_shares
        self.float_shares += issue_shares
        self.cash_reserve += amount
        
        # 更新每股收益
        self.eps = self.annual_profit / Decimal(self.total_shares)
        
        # 记录操作
        operation = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "type": "private_placement",
            "shares": issue_shares,
            "price": float(issue_price),
            "amount": float(amount),
            "total_shares_after": self.total_shares,
            "float_shares_after": self.float_shares,
            "cash_reserve_after": float(self.cash_reserve),
            "eps_after": float(self.eps)
        }
        self.operations.append(operation)
        
        logger.info(f"执行定向增发: {issue_shares}股 @ {issue_price}元, 募集资金: {amount}元")
        logger.info(f"增发后总股本: {self.total_shares}股, 流通股本: {self.float_shares}股")
        logger.info(f"增发后现金储备: {self.cash_reserve}元, 每股收益: {self.eps}元")
        
        # 定向增发可能会影响股价
        price_impact = random.uniform(-0.05, 0.02)  # -5%~2%的影响
        self.stock_price = self.stock_price * (1 + Decimal(str(price_impact)))
        logger.info(f"定向增发对股价的影响: {price_impact*100:+.2f}%, 新股价: {self.stock_price}元")
        
        return {
            "success": True,
            "shares": issue_shares,
            "price": float(issue_price),
            "amount": float(amount)
        }
    
    def run_simulation(self, years: int = 1) -> None:
        """运行市值管理模拟
        
        Args:
            years: 模拟年数
        """
        logger.info(f"开始市值管理模拟: {years}年")
        
        # 每年的交易日约为250天
        trading_days = years * 250
        
        for day in range(trading_days):
            # 更新市场价格
            self.update_market_price()
            
            # 每季度考虑回购
            if day % 60 == 0:  # 约每季度一次
                # 如果股价低于PE 15，考虑回购
                if self.pe_ratio < 15:
                    logger.info(f"当前PE({self.pe_ratio:.2f})低于15，考虑回购")
                    self.execute_stock_buyback()
            
            # 每年考虑分红
            if day % 250 == 249:  # 每年年末
                logger.info("年末考虑分红")
                self.execute_dividend_payment()
                
                # 更新年度利润(假设每年增长10%-20%)
                profit_growth = random.uniform(0.1, 0.2)
                self.annual_profit = self.annual_profit * (1 + Decimal(str(profit_growth)))
                self.eps = self.annual_profit / Decimal(self.total_shares)
                logger.info(f"更新年度利润: {self.annual_profit}元, 增长: {profit_growth*100:.2f}%")
            
            # 每两年考虑一次股票拆分
            if day % 500 == 499:
                # 如果股价高于100元，考虑拆分
                if self.stock_price > 100:
                    logger.info(f"当前股价({self.stock_price})高于100元，考虑拆分")
                    self.execute_stock_split()
            
            # 每三年考虑一次股权激励
            if day % 750 == 749:
                incentive_shares = int(self.total_shares * Decimal("0.01"))  # 1%的股本
                logger.info(f"三年期考虑股权激励，计划激励股份: {incentive_shares}股")
                self.execute_equity_incentive(incentive_shares)
            
            # 每五年考虑一次定向增发
            if day % 1250 == 1249:
                # 如果PE高于30，考虑定向增发
                if self.pe_ratio > 30:
                    placement_amount = self.market_value * Decimal("0.05")  # 市值的5%
                    logger.info(f"当前PE({self.pe_ratio:.2f})高于30，考虑定向增发，计划募集: {placement_amount}元")
                    self.execute_private_placement(placement_amount)
        
        logger.info(f"市值管理模拟结束，持续时间: {years}年")
        logger.info(f"最终状态: 股价={self.stock_price}元, 总市值={self.market_value/100000000:.2f}亿元")
        logger.info(f"总股本={self.total_shares}股, 流通股本={self.float_shares}股")
        logger.info(f"每股收益={self.eps}元, 市盈率={self.pe_ratio:.2f}")
        
        # 保存操作记录
        self.save_results()
        
        # 绘制图表
        self.plot_results()
    
    def save_results(self) -> None:
        """保存操作结果"""
        output_dir = "/Users/hongyaotang/src/py/pyagent/output"
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存操作记录
        if self.operations:
            operations_df = pd.DataFrame(self.operations)
            operations_path = f"{output_dir}/hs_market_value_operations_{int(time.time())}.csv"
            operations_df.to_csv(operations_path, index=False)
            logger.info(f"操作记录已保存到: {operations_path}")
        
        # 保存价格历史
        if self.price_history:
            price_df = pd.DataFrame(self.price_history)
            price_path = f"{output_dir}/hs_market_value_price_{int(time.time())}.csv"
            price_df.to_csv(price_path, index=False)
            logger.info(f"价格历史已保存到: {price_path}")
    
    def plot_results(self) -> None:
        """绘制结果图表"""
        if not self.price_history:
            logger.warning("没有价格历史记录，无法绘制图表")
            return
        
        # 创建价格DataFrame
        price_df = pd.DataFrame(self.price_history)
        price_df["date"] = pd.to_datetime(price_df["date"])
        
        # 创建操作DataFrame
        operations_df = pd.DataFrame(self.operations)
        if not operations_df.empty:
            operations_df["date"] = pd.to_datetime(operations_df["date"])
        
        # 绘制价格和市值图表
        plt.figure(figsize=(12, 8))
        
        # 绘制子图1: 股价和操作
        plt.subplot(2, 1, 1)
        plt.plot(price_df["date"], price_df["price"], 'b-', label="股价")
        
        # 绘制各类操作点
        if not operations_df.empty:
            # 回购点
            buybacks = operations_df[operations_df["type"] == "buyback"]
            if not buybacks.empty:
                plt.scatter(buybacks["date"], buybacks["price"], color="green", label="回购", marker="^", s=100)
            
            # 分红点
            dividends = operations_df[operations_df["type"] == "dividend"]
            if not dividends.empty:
                # 使用最近的价格
                for idx, row in dividends.iterrows():
                    date = row["date"]
                    price_at_date = price_df[price_df["date"] <= date]["price"].iloc[-1] if not price_df[price_df["date"] <= date].empty else 0
                    plt.scatter(date, price_at_date, color="red", label="分红" if idx == dividends.index[0] else "", marker="v", s=100)
            
            # 拆分点
            splits = operations_df[operations_df["type"] == "split"]
            if not splits.empty:
                plt.scatter(splits["date"], splits["price_after"], color="purple", label="拆分", marker="s", s=100)
            
            # 股权激励点
            incentives = operations_df[operations_df["type"] == "equity_incentive"]
            if not incentives.empty:
                plt.scatter(incentives["date"], incentives["price"], color="orange", label="股权激励", marker="*", s=100)
            
            # 定向增发点
            placements = operations_df[operations_df["type"] == "private_placement"]
            if not placements.empty:
                plt.scatter(placements["date"], placements["price"], color="brown", label="定向增发", marker="D", s=100)
        
        plt.title("恒生电子市值管理 - 股价和操作")
        plt.xlabel("日期")
        plt.ylabel("股价 (元)")
        plt.legend()
        plt.grid(True)
        
        # 绘制子图2: 市值和市盈率
        plt.subplot(2, 1, 2)
        plt.plot(price_df["date"], price_df["market_value"] / 100000000, 'g-', label="总市值(亿元)")
        
        # 创建第二个Y轴
        ax2 = plt.twinx()
        ax2.plot(price_df["date"], price_df["pe_ratio"], 'r-', label="市盈率")
        
        plt.title("恒生电子市值管理 - 总市值和市盈率")
        plt.xlabel("日期")
        plt.ylabel("总市值 (亿元)")
        ax2.set_ylabel("市盈率")
        
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
        
        output_path = f"{output_dir}/hs_market_value_manager_{int(time.time())}.png"
        plt.savefig(output_path)
        logger.info(f"市值管理图表已保存到: {output_path}")
        
        # 关闭图表
        plt.close()

def main():
    """主函数"""
    # 创建市值管理器
    market_value_manager = HSMarketValueManager()
    
    # 运行模拟
    market_value_manager.run_simulation(years=5)

if __name__ == "__main__":
    main()