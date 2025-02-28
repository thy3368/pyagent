from openai import OpenAI
import json
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import matplotlib.pyplot as plt

class FinanceAgent:
    def __init__(self):
        self.client = OpenAI(
            api_key="sk-XvWvy8rf8ewno0vVFmtgOMidGb5i3h1qNQmer7bE2buY6hlK",
            base_url="https://tbnx.plus7.plus/v1"
        )
        self.transactions = []
        self.budgets = {}
        self.investment_portfolio = {}
        
    def add_transaction(self, amount: float, category: str, description: str, 
                       transaction_type: str = "expense", date: Optional[str] = None):
        """添加收支记录"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
            
        transaction = {
            "date": date,
            "amount": amount,
            "category": category,
            "description": description,
            "type": transaction_type
        }
        self.transactions.append(transaction)
        return "交易记录已添加"
        
    def set_budget(self, category: str, amount: float):
        """设置预算"""
        self.budgets[category] = amount
        return f"已设置 {category} 类别的预算为 {amount} 元"
        
    def analyze_spending(self) -> str:
        """分析支出情况"""
        if not self.transactions:
            return "暂无交易记录"
            
        df = pd.DataFrame(self.transactions)
        
        # 计算各类别支出
        expenses = df[df['type'] == 'expense'].groupby('category')['amount'].sum()
        
        # 计算预算使用情况
        budget_analysis = []
        for category, spent in expenses.items():
            budget = self.budgets.get(category, 0)
            if budget > 0:
                percentage = (spent / budget) * 100
                status = "超支" if percentage > 100 else "正常"
                budget_analysis.append(f"{category}: 支出 {spent:.2f}元 / 预算 {budget:.2f}元 ({percentage:.1f}%) - {status}")
        
        return "\n".join(budget_analysis)
        
    def get_financial_advice(self, income: float, savings_goal: float) -> str:
        """获取理财建议"""
        context = {
            "monthly_income": income,
            "savings_goal": savings_goal,
            "current_expenses": self.analyze_spending(),
            "budgets": self.budgets
        }
        
        prompt = f"""作为一个财务顾问，请基于以下信息提供理财建议：

月收入：{income} 元
储蓄目标：{savings_goal} 元
当前支出情况：
{context['current_expenses']}

请提供：
1. 支出优化建议
2. 储蓄策略
3. 投资组合建议
4. 理财目标规划"""

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    def visualize_spending(self):
        """可视化支出分析"""
        if not self.transactions:
            return "暂无数据可视化"
            
        df = pd.DataFrame(self.transactions)
        expenses = df[df['type'] == 'expense']
        
        # 创建饼图
        plt.figure(figsize=(10, 6))
        expenses.groupby('category')['amount'].sum().plot(kind='pie', autopct='%1.1f%%')
        plt.title('支出类别分布')
        plt.axis('equal')
        plt.savefig('/Users/hongyaotang/src/py/pyagent/data/spending_analysis.png')
        plt.close()
        
        return "支出分析图表已生成"

def main():
    agent = FinanceAgent()
    
    print("财务助手已启动")
    print("\n可用命令：")
    print("1. 添加交易 - add")
    print("2. 设置预算 - budget")
    print("3. 分析支出 - analyze")
    print("4. 获取建议 - advice")
    print("5. 可视化分析 - viz")
    print("输入 'exit' 退出")
    
    while True:
        command = input("\n请输入命令: ").lower()
        
        if command == "exit":
            print("再见！")
            break
            
        elif command == "add":
            amount = float(input("金额: "))
            category = input("类别: ")
            description = input("描述: ")
            type_ = input("类型(收入/支出): ")
            result = agent.add_transaction(
                amount, category, description,
                "income" if type_ == "收入" else "expense"
            )
            print(result)
            
        elif command == "budget":
            category = input("类别: ")
            amount = float(input("预算金额: "))
            result = agent.set_budget(category, amount)
            print(result)
            
        elif command == "analyze":
            result = agent.analyze_spending()
            print("\n支出分析：")
            print(result)
            
        elif command == "advice":
            income = float(input("月收入: "))
            savings_goal = float(input("储蓄目标: "))
            advice = agent.get_financial_advice(income, savings_goal)
            print("\n理财建议：")
            print(advice)
            
        elif command == "viz":
            result = agent.visualize_spending()
            print(result)
            
        else:
            print("未知命令")

if __name__ == "__main__":
    main()