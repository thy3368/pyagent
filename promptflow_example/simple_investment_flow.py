from promptflow import tool, flow
import json

# 定义一个简单的市场分析工具
@tool
def analyze_market(symbol: str) -> dict:
    """简单的市场分析工具"""
    # 这里使用模拟数据，实际应用中可以连接到真实数据源
    market_data = {
        "AAPL": {"trend": "上涨", "risk_level": 3},
        "MSFT": {"trend": "震荡", "risk_level": 4},
        "GOOGL": {"trend": "下跌", "risk_level": 6}
    }
    
    return market_data.get(symbol, {"trend": "未知", "risk_level": 5})

# 定义投资建议生成工具
@tool
def generate_investment_advice(market_analysis: dict, risk_preference: int) -> str:
    """生成投资建议"""
    trend = market_analysis.get("trend", "未知")
    market_risk = market_analysis.get("risk_level", 5)
    
    # 根据市场趋势和风险偏好生成建议
    if trend == "上涨" and risk_preference >= market_risk:
        advice = "建议买入，市场趋势向好，符合您的风险偏好。"
    elif trend == "下跌" and risk_preference <= market_risk:
        advice = "建议观望或少量卖出，市场趋势不佳，注意控制风险。"
    else:
        advice = "建议持仓观望，市场震荡，等待更明确的信号。"
    
    return advice

# 定义主流程
@flow
def investment_advice_flow(symbol: str, risk_preference: int) -> dict:
    """简单的投资建议流程"""
    # 1. 分析市场
    market_analysis = analyze_market(symbol)
    
    # 2. 生成投资建议
    advice = generate_investment_advice(market_analysis, risk_preference)
    
    # 3. 返回结果
    return {
        "symbol": symbol,
        "market_analysis": market_analysis,
        "risk_preference": risk_preference,
        "investment_advice": advice
    }