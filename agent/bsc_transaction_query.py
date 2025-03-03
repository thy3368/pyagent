import requests
import json
import pandas as pd
from datetime import datetime
import os
import argparse
from typing import List, Dict, Any

class BscTransactionQuery:
    def __init__(self, api_key=None):
        """初始化 BSC 交易查询工具"""
        # 如果没有提供 API key，可以使用免费的 API，但有请求限制
        self.api_key = api_key or "BIHIR1FTN3T7Z1K1QQRW39JUJ2DNGUERVH"  # 替换为你的 BscScan API key
        self.base_url = "https://api.bscscan.com/api"
        
    def get_contract_transactions(self, contract_address: str, page: int = 1, offset: int = 100, filter_address: str = None) -> List[Dict[str, Any]]:
        """获取合约交易记录"""
        params = {
            "module": "account",
            "action": "txlist",
            "address": contract_address,
            "startblock": 0,
            "endblock": 99999999,
            "page": page,
            "offset": offset,  # 每页记录数
            "sort": "desc",    # 按时间降序排列
            "apikey": self.api_key
        }
        
        response = requests.get(self.base_url, params=params)
        data = response.json()
        
        if data["status"] == "1":
            transactions = data["result"]
            
            # 如果提供了过滤地址，则只返回与该地址相关的交易
            if filter_address:
                filter_address = filter_address.lower()
                filtered_transactions = []
                for tx in transactions:
                    if tx.get("from", "").lower() == filter_address or tx.get("to", "").lower() == filter_address:
                        filtered_transactions.append(tx)
                return filtered_transactions
            else:
                return transactions
        else:
            print(f"查询失败: {data['message']}")
            return []
            
    def get_token_transfers(self, contract_address: str, page: int = 1, offset: int = 100, filter_address: str = None) -> List[Dict[str, Any]]:
        """获取代币转账记录"""
        params = {
            "module": "account",
            "action": "tokentx",
            "contractaddress": contract_address,
            "page": page,
            "offset": offset,
            "sort": "desc",
            "apikey": self.api_key
        }
        
        response = requests.get(self.base_url, params=params)
        data = response.json()
        
        if data["status"] == "1":
            transfers = data["result"]
            
            # 如果提供了过滤地址，则只返回与该地址相关的转账
            if filter_address:
                filter_address = filter_address.lower()
                filtered_transfers = []
                for transfer in transfers:
                    if transfer.get("from", "").lower() == filter_address or transfer.get("to", "").lower() == filter_address:
                        filtered_transfers.append(transfer)
                return filtered_transfers
            else:
                return transfers
        else:
            print(f"查询失败: {data['message']}")
            return []
    
    def get_contract_info(self, contract_address: str) -> Dict[str, Any]:
        """获取合约信息"""
        params = {
            "module": "contract",
            "action": "getsourcecode",
            "address": contract_address,
            "apikey": self.api_key
        }
        
        response = requests.get(self.base_url, params=params)
        data = response.json()
        
        if data["status"] == "1":
            return data["result"][0]
        else:
            print(f"查询失败: {data['message']}")
            return {}
    
    def format_transactions(self, transactions: List[Dict[str, Any]]) -> pd.DataFrame:
        """格式化交易数据"""
        if not transactions:
            return pd.DataFrame()
            
        # 提取关键字段
        formatted_txs = []
        for tx in transactions:
            # 尝试解析输入数据，提取代币数量
            token_amount = 0
            token_method = ""
            token_recipient = ""
            
            if tx.get("input") and tx.get("input").startswith("0x"):
                input_data = tx.get("input")
                # 检查是否为代币转账方法 (transfer: 0xa9059cbb)
                if input_data.startswith("0xa9059cbb"):
                    token_method = "transfer"
                    # 尝试提取接收地址 (位于方法签名之后的32字节)
                    if len(input_data) >= 74:
                        try:
                            address_hex = input_data[10:74]
                            # 补全地址格式
                            token_recipient = "0x" + address_hex[-40:]
                        except:
                            token_recipient = ""
                    
                    # 尝试从输入数据中提取数量 (位于方法签名和地址之后)
                    if len(input_data) >= 138:  # 0x + 8字节方法签名 + 32字节地址 + 32字节数量
                        try:
                            # 提取数量部分 (最后32字节)
                            amount_hex = input_data[74:138]
                            token_amount = int(amount_hex, 16) / 1e18  # 假设精度为18
                        except:
                            token_amount = 0
                # 检查是否为批量转账方法 (transferFrom: 0x23b872dd)
                elif input_data.startswith("0x23b872dd"):
                    token_method = "transferFrom"
                    # 尝试提取发送和接收地址
                    if len(input_data) >= 138:
                        try:
                            from_address_hex = input_data[10:74]
                            to_address_hex = input_data[74:138]
                            token_recipient = "0x" + to_address_hex[-40:]
                        except:
                            token_recipient = ""
                    
                    # 尝试提取数量
                    if len(input_data) >= 202:
                        try:
                            amount_hex = input_data[138:202]
                            token_amount = int(amount_hex, 16) / 1e18
                        except:
                            token_amount = 0
                
            formatted_tx = {
                "交易哈希": tx.get("hash"),
                "区块号": int(tx.get("blockNumber", 0)),
                "时间戳": datetime.fromtimestamp(int(tx.get("timeStamp", 0))),
                "发送方": tx.get("from"),
                "接收方": tx.get("to"),
                "价值(BNB)": float(tx.get("value", 0)) / 1e18,  # 转换为 BNB
                "代币方法": token_method,
                "代币接收方": token_recipient,
                "代币数量": token_amount,
                "交易费用(BNB)": float(tx.get("gasPrice", 0)) * float(tx.get("gasUsed", 0)) / 1e18,
                "状态": "成功" if tx.get("txreceipt_status") == "1" else "失败"
            }
            formatted_txs.append(formatted_tx)
            
        return pd.DataFrame(formatted_txs)
    
    def format_token_transfers(self, transfers: List[Dict[str, Any]]) -> pd.DataFrame:
        """格式化代币转账数据"""
        if not transfers:
            return pd.DataFrame()
            
        # 提取关键字段
        formatted_transfers = []
        for transfer in transfers:
            formatted_transfer = {
                "交易哈希": transfer.get("hash"),
                "区块号": int(transfer.get("blockNumber", 0)),
                "时间戳": datetime.fromtimestamp(int(transfer.get("timeStamp", 0))),
                "发送方": transfer.get("from"),
                "接收方": transfer.get("to"),
                "代币名称": transfer.get("tokenName"),
                "代币符号": transfer.get("tokenSymbol"),
                "数量": float(transfer.get("value", 0)) / (10 ** int(transfer.get("tokenDecimal", 18))),
            }
            formatted_transfers.append(formatted_transfer)
            
        return pd.DataFrame(formatted_transfers)
    
    def save_to_csv(self, df: pd.DataFrame, filename: str) -> str:
        """保存数据到 CSV 文件"""
        if df.empty:
            return "没有数据可保存"
            
        output_dir = "/Users/hongyaotang/src/py/pyagent/output"
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = f"{output_dir}/{filename}"
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        return f"数据已保存到 {output_path}"

# 在BscTransactionQuery类中添加新方法
    def get_account_balance(self, address: str) -> Dict[str, Any]:
        """获取账户BNB余额"""
        params = {
            "module": "account",
            "action": "balance",
            "address": address,
            "tag": "latest",
            "apikey": self.api_key
        }
        
        response = requests.get(self.base_url, params=params)
        data = response.json()
        
        if data["status"] == "1":
            balance_wei = int(data["result"])
            balance_bnb = balance_wei / 1e18
            return {
                "address": address,
                "balance_wei": balance_wei,
                "balance_bnb": balance_bnb
            }
        else:
            print(f"查询余额失败: {data['message']}")
            return {"address": address, "balance_wei": 0, "balance_bnb": 0}
    
    def get_token_balance(self, contract_address: str, wallet_address: str) -> Dict[str, Any]:
        """获取代币余额"""
        params = {
            "module": "account",
            "action": "tokenbalance",
            "contractaddress": contract_address,
            "address": wallet_address,
            "tag": "latest",
            "apikey": self.api_key
        }
        
        response = requests.get(self.base_url, params=params)
        data = response.json()
        
        if data["status"] == "1":
            balance = int(data["result"])
            # 默认假设代币精度为18，实际应用中应该从合约获取
            balance_token = balance / 1e18
            return {
                "contract": contract_address,
                "wallet": wallet_address,
                "balance_raw": balance,
                "balance_token": balance_token
            }
        else:
            print(f"查询代币余额失败: {data['message']}")
            return {
                "contract": contract_address,
                "wallet": wallet_address,
                "balance_raw": 0,
                "balance_token": 0
            }

# 在main函数中修改输出部分
def main():
    parser = argparse.ArgumentParser(description='查询币安智能链上合约交易明细')
    parser.add_argument('--address', type=str, default="0x2383596EFa3A0fc13EfdCd776410deFf25017417",
                        help='合约地址')
    parser.add_argument('--api-key', type=str, help='BscScan API Key')
    parser.add_argument('--page', type=int, default=1, help='页码')
    parser.add_argument('--limit', type=int, default=100, help='每页记录数')
    parser.add_argument('--filter', type=str, help='过滤特定账户地址的交易')
    
    args = parser.parse_args()
    
    query = BscTransactionQuery(api_key=args.api_key)
    
    # ... 现有代码 ...
    
    # 在查询合约信息后添加余额查询
    print(f"正在查询合约 {args.address} 的信息...")
    contract_info = query.get_contract_info(args.address)
    if contract_info:
        print(f"合约名称: {contract_info.get('ContractName', '未知')}")
        print(f"编译器版本: {contract_info.get('CompilerVersion', '未知')}")
        print(f"是否已验证: {'是' if contract_info.get('ABI') != 'Contract source code not verified' else '否'}")
        
        # 查询合约账户余额
        balance_info = query.get_account_balance(args.address)
        print(f"合约账户余额: {balance_info['balance_bnb']:.6f} BNB")
        
        # 如果提供了过滤地址，也查询该地址的余额
        if args.filter:
            filter_balance = query.get_account_balance(args.filter)
            print(f"过滤地址余额: {filter_balance['balance_bnb']:.6f} BNB")
            
            # 查询过滤地址持有的合约代币余额
            token_balance = query.get_token_balance(args.address, args.filter)
            print(f"过滤地址持有代币余额: {token_balance['balance_token']:.6f}")
    
    filter_text = f"(过滤地址: {args.filter})" if args.filter else "0x65Ba368021AE8F0360ab4f90D397E9D424bC0F77"
    print(f"\n正在获取合约 {args.address} 的交易记录...{filter_text}")
    transactions = query.get_contract_transactions(args.address, args.page, args.limit, args.filter)
    # 在main函数中找到以下部分并修改
    if transactions:
        print(f"找到 {len(transactions)} 条交易记录")
        tx_df = query.format_transactions(transactions)
        
        # 调整显示的列，确保代币数量信息被展示
        display_columns = ["交易哈希", "时间戳", "发送方", "接收方", "代币方法", "代币接收方", "代币数量", "价值(BNB)", "状态"]
        print("\n交易记录示例:")
        pd.set_option('display.max_columns', None)  # 显示所有列
        pd.set_option('display.width', 1000)  # 设置显示宽度
        pd.set_option('display.max_colwidth', 30)  # 设置列宽度
        print(tx_df[display_columns].head(5))
        
        filename = f"bsc_transactions_{args.address[-6:]}"
        if args.filter:
            filename += f"_filtered_{args.filter[-6:]}"
        filename += ".csv"
        
        save_result = query.save_to_csv(tx_df, filename)
        print(save_result)
    else:
        print("未找到交易记录")
    
    print(f"\n正在获取合约 {args.address} 的代币转账记录...{filter_text}")
    transfers = query.get_token_transfers(args.address, args.page, args.limit, args.filter)
    if transfers:
        print(f"找到 {len(transfers)} 条代币转账记录")
        transfer_df = query.format_token_transfers(transfers)
        print("\n代币转账记录示例:")
        print(transfer_df.head(5))
        
        filename = f"bsc_token_transfers_{args.address[-6:]}"
        if args.filter:
            filename += f"_filtered_{args.filter[-6:]}"
        filename += ".csv"
        
        save_result = query.save_to_csv(transfer_df, filename)
        print(save_result)
    else:
        print("未找到代币转账记录")

if __name__ == "__main__":
    main()