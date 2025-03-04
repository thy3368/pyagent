import os
import json
import time
import logging
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd
import matplotlib.pyplot as plt
import requests
from io import StringIO

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

# 定义默认参数
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email': ['your_email@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# 创建DAG
dag = DAG(
    'hs_market_value_analysis',
    default_args=default_args,
    description='恒生电子市值分析流程',
    schedule_interval=timedelta(days=1),
    start_date=days_ago(1),
    tags=['stock', 'market_value', 'analysis'],
)

# 定义数据目录
DATA_DIR = "/Users/hongyaotang/src/py/pyagent/data"
OUTPUT_DIR = "/Users/hongyaotang/src/py/pyagent/output"

# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 定义任务函数
def fetch_stock_data(**kwargs):
    """获取恒生电子股票数据"""
    stock_code = "600570.SH"
    today = datetime.now().strftime("%Y%m%d")
    
    # 这里模拟从API获取数据，实际应用中应替换为真实API调用
    # 例如使用tushare、baostock等库获取实际数据
    
    # 模拟数据
    dates = []
    prices = []
    volumes = []
    
    # 生成过去30天的模拟数据
    for i in range(30):
        date = (datetime.now() - timedelta(days=30-i)).strftime("%Y-%m-%d")
        dates.append(date)
        
        # 模拟价格和成交量
        price = 55.0 + (i % 10) * 0.5
        volume = 10000000 + (i % 5) * 1000000
        
        prices.append(price)
        volumes.append(volume)
    
    # 创建DataFrame
    df = pd.DataFrame({
        "date": dates,
        "price": prices,
        "volume": volumes
    })
    
    # 保存数据
    output_path = f"{DATA_DIR}/hs_stock_data_{today}.csv"
    df.to_csv(output_path, index=False)
    
    return output_path

def calculate_market_value(**kwargs):
    """计算市值指标"""
    ti = kwargs['ti']
    stock_data_path = ti.xcom_pull(task_ids='fetch_stock_data')
    today = datetime.now().strftime("%Y%m%d")
    
    # 读取股票数据
    df = pd.read_csv(stock_data_path)
    
    # 公司基本信息
    total_shares = 1000000000  # 总股本(股)
    float_shares = 800000000   # 流通股本(股)
    annual_profit = 2000000000.00  # 年度利润(元)
    
    # 计算市值指标
    df['total_market_value'] = df['price'] * total_shares
    df['float_market_value'] = df['price'] * float_shares
    df['eps'] = annual_profit / total_shares
    df['pe_ratio'] = df['price'] / df['eps']
    
    # 保存结果
    output_path = f"{DATA_DIR}/hs_market_value_{today}.csv"
    df.to_csv(output_path, index=False)
    
    return output_path

def generate_market_value_report(**kwargs):
    """生成市值分析报告"""
    ti = kwargs['ti']
    market_value_path = ti.xcom_pull(task_ids='calculate_market_value')
    today = datetime.now().strftime("%Y%m%d")
    
    # 读取市值数据
    df = pd.read_csv(market_value_path)
    df['date'] = pd.to_datetime(df['date'])
    
    # 绘制图表
    plt.figure(figsize=(12, 8))
    
    # 绘制子图1: 股价走势
    plt.subplot(2, 1, 1)
    plt.plot(df['date'], df['price'], 'b-', label="股价")
    plt.title("恒生电子股价走势")
    plt.xlabel("日期")
    plt.ylabel("股价 (元)")
    plt.grid(True)
    plt.legend()
    
    # 绘制子图2: 市值和市盈率
    plt.subplot(2, 1, 2)
    plt.plot(df['date'], df['total_market_value'] / 100000000, 'g-', label="总市值(亿元)")
    
    # 创建第二个Y轴
    ax2 = plt.twinx()
    ax2.plot(df['date'], df['pe_ratio'], 'r-', label="市盈率")
    
    plt.title("恒生电子市值和市盈率")
    plt.xlabel("日期")
    plt.ylabel("总市值 (亿元)")
    ax2.set_ylabel("市盈率")
    
    # 合并两个图例
    lines1, labels1 = plt.gca().get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc="upper left")
    
    plt.grid(True)
    plt.tight_layout()
    
    # 保存图表
    chart_path = f"{OUTPUT_DIR}/hs_market_value_chart_{today}.png"
    plt.savefig(chart_path)
    plt.close()
    
    # 生成简单的HTML报告
    html_content = f"""
    <html>
    <head>
        <title>恒生电子市值分析报告 - {today}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #333366; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .chart {{ margin: 20px 0; max-width: 100%; }}
        </style>
    </head>
    <body>
        <h1>恒生电子市值分析报告</h1>
        <p>生成日期: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        
        <h2>市值概览</h2>
        <table>
            <tr>
                <th>指标</th>
                <th>最新值</th>
                <th>30天最高</th>
                <th>30天最低</th>
                <th>30天平均</th>
            </tr>
            <tr>
                <td>股价(元)</td>
                <td>{df['price'].iloc[-1]:.2f}</td>
                <td>{df['price'].max():.2f}</td>
                <td>{df['price'].min():.2f}</td>
                <td>{df['price'].mean():.2f}</td>
            </tr>
            <tr>
                <td>总市值(亿元)</td>
                <td>{df['total_market_value'].iloc[-1]/100000000:.2f}</td>
                <td>{df['total_market_value'].max()/100000000:.2f}</td>
                <td>{df['total_market_value'].min()/100000000:.2f}</td>
                <td>{df['total_market_value'].mean()/100000000:.2f}</td>
            </tr>
            <tr>
                <td>市盈率</td>
                <td>{df['pe_ratio'].iloc[-1]:.2f}</td>
                <td>{df['pe_ratio'].max():.2f}</td>
                <td>{df['pe_ratio'].min():.2f}</td>
                <td>{df['pe_ratio'].mean():.2f}</td>
            </tr>
        </table>
        
        <h2>市值走势图</h2>
        <img src="hs_market_value_chart_{today}.png" class="chart" alt="市值走势图">
        
        <h2>数据表</h2>
        <table>
            <tr>
                <th>日期</th>
                <th>股价(元)</th>
                <th>总市值(亿元)</th>
                <th>市盈率</th>
            </tr>
    """
    
    # 添加最近10天的数据行
    for _, row in df.tail(10).iterrows():
        html_content += f"""
            <tr>
                <td>{row['date'].strftime('%Y-%m-%d')}</td>
                <td>{row['price']:.2f}</td>
                <td>{row['total_market_value']/100000000:.2f}</td>
                <td>{row['pe_ratio']:.2f}</td>
            </tr>
        """
    
    html_content += """
        </table>
    </body>
    </html>
    """
    
    # 保存HTML报告
    report_path = f"{OUTPUT_DIR}/hs_market_value_report_{today}.html"
    with open(report_path, 'w') as f:
        f.write(html_content)
    
    return report_path

def send_notification(**kwargs):
    """发送通知"""
    ti = kwargs['ti']
    report_path = ti.xcom_pull(task_ids='generate_market_value_report')
    
    # 这里可以实现发送邮件或其他通知的逻辑
    # 例如使用airflow.operators.email_operator.EmailOperator
    
    print(f"市值分析报告已生成: {report_path}")
    print("通知已发送")
    
    return True

# 定义任务
fetch_data_task = PythonOperator(
    task_id='fetch_stock_data',
    python_callable=fetch_stock_data,
    provide_context=True,
    dag=dag,
)

calculate_market_value_task = PythonOperator(
    task_id='calculate_market_value',
    python_callable=calculate_market_value,
    provide_context=True,
    dag=dag,
)

generate_report_task = PythonOperator(
    task_id='generate_market_value_report',
    python_callable=generate_market_value_report,
    provide_context=True,
    dag=dag,
)

send_notification_task = PythonOperator(
    task_id='send_notification',
    python_callable=send_notification,
    provide_context=True,
    dag=dag,
)

# 定义任务依赖关系
fetch_data_task >> calculate_market_value_task >> generate_report_task >> send_notification_task