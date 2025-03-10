# pyagent

- 开发目标：基于BSC链上SQV代币的交易和钱包数据，构建知识图谱并可视化异常庄家行为。

**步骤分解：**

1. **数据获取**
   - 使用`bscscan-python`或`web3.py`从BSCScan API提取SQV代币交易数据（需API密钥）。
   - 关键字段：交易哈希、时间戳、发送方、接收方、代币数量、Gas费用、合约地址。
   - 示例代码框架：
     ```python
     from bscscan import BscScan
     async with BscScan(YOUR_API_KEY) as client:
         txs = await client.get_token_transfer_events_by_address(
             address=TOKEN_CONTRACT,
             startblock=0,
             endblock=99999999,
             sort="asc"
         )
     ```

2. **数据预处理**
   - 清洗数据：过滤无效交易，标准化地址格式。
   - 标记大额交易（如超过总供应量的1%）、高频地址。
   - 使用`pandas`构建交易关系矩阵：
     ```python
     import pandas as pd
     df = pd.DataFrame(txs)
     df['value'] = df['value'].astype(float) / 1e18  # 代币精度标准化
     ```

3. **知识图谱构建**
   - 节点：钱包地址（属性：交易次数、总金额、首次/末次交易时间）。
   - 边：交易关系（权重=金额，属性=时间戳、Gas消耗）。
   - 使用`networkx`或`pyvis`创建图谱：
     ```python
     import networkx as nx
     G = nx.DiGraph()
     for _, tx in df.iterrows():
         G.add_edge(tx['from'], tx['to'], weight=tx['value'], timestamp=tx['timeStamp'])
     ```

4. **异常行为检测逻辑**
   - **模式1：对敲交易**
     - 检测双向边：同一对地址间频繁双向转账。
     ```python
     bidirectional_edges = [(u, v) for (u, v) in G.edges() if G.has_edge(v, u)]
     ```
   - **模式2：资金汇集**
     - 识别入度/出度失衡的枢纽节点（如某个地址入度>100且出度<5）。
   - **模式3：时间聚类**
     - 使用时间窗口分析（如1小时内同一地址发起50+交易）。

5. **可视化增强**
   - 用颜色标记节点属性（红色=大额接收方，蓝色=高频发送方）。
   - 动态过滤：通过滑块控制显示交易金额阈值。
   - 示例代码（PyVis）：
     ```python
     from pyvis.network import Network
     net = Network(notebook=True, directed=True)
     net.from_nx(G)
     net.show("sqv_graph.html")
     ```

6. **输出交付**
   - 生成交互式HTML图谱文件。
   - 输出可疑地址列表及关联证据（如：地址0xabc在24小时内与15个地址发生环状交易）。

**优化提示：**
- 添加Layer-2数据（如PancakeSwap流动性池变动）
- 集成机器学习模型（使用`scikit-learn`检测聚类异常）
- 使用图数据库（neo4j）存储复杂关系