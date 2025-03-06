from promptflow.core import run_flow

def main():
    # 要分析的股票
    symbols = ["AAPL", "MSFT", "GOOGL"]
    # 用户风险偏好(1-10)
    risk_preference = 5
    
    print("=== 简单投资建议系统 ===")
    
    for symbol in symbols:
        print(f"\n分析股票: {symbol}")
        
        # 运行流程
        result = run_flow(
            flow_file="simple_investment_flow.py",
            flow_name="investment_advice_flow",
            inputs={
                "symbol": symbol,
                "risk_preference": risk_preference
            }
        )
        
        # 打印结果
        print(f"市场趋势: {result['market_analysis']['trend']}")
        print(f"风险等级: {result['market_analysis']['risk_level']}")
        print(f"投资建议: {result['investment_advice']}")

if __name__ == "__main__":
    main()