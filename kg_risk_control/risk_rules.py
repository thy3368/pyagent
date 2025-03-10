from typing import Dict, List, Any, Callable
import logging

logger = logging.getLogger("KG_Risk_Control")

class RiskRule:
    """风控规则基类"""
    
    def __init__(self, rule_id: str, name: str, description: str, risk_level: int):
        """初始化风控规则
        
        Args:
            rule_id: 规则ID
            name: 规则名称
            description: 规则描述
            risk_level: 风险等级(1-10)
        """
        self.rule_id = rule_id
        self.name = name
        self.description = description
        self.risk_level = risk_level
    
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """评估风险
        
        Args:
            context: 评估上下文
            
        Returns:
            评估结果
        """
        raise NotImplementedError("子类必须实现evaluate方法")

class CircularTransactionRule(RiskRule):
    """环形交易检测规则"""
    
    def __init__(self):
        super().__init__(
            rule_id="R001",
            name="环形交易检测",
            description="检测资金在多个账户间形成环形流动的模式，可能是洗钱或欺诈行为",
            risk_level=8
        )
    
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """评估是否存在环形交易
        
        Args:
            context: 包含知识图谱和交易信息的上下文
            
        Returns:
            评估结果
        """
        kg = context.get('knowledge_graph')
        account_id = context.get('account_id')
        
        if not kg or not account_id:
            return {
                'rule_id': self.rule_id,
                'triggered': False,
                'risk_level': 0,
                'details': "缺少必要的评估信息"
            }
        
        # 查找从账户出发并回到账户的路径
        cycles = []
        
        # 使用NetworkX的简单环路查找
        try:
            for cycle in kg.graph.simple_cycles():
                if account_id in cycle and len(cycle) >= 3:
                    cycles.append(cycle)
        except Exception as e:
            logger.error(f"查找环路时出错: {str(e)}")
        
        if cycles:
            return {
                'rule_id': self.rule_id,
                'triggered': True,
                'risk_level': self.risk_level,
                'details': {
                    'cycles': cycles,
                    'cycle_count': len(cycles)
                }
            }
        else:
            return {
                'rule_id': self.rule_id,
                'triggered': False,
                'risk_level': 0,
                'details': "未检测到环形交易"
            }

class SharedAddressRule(RiskRule):
    """共享地址检测规则"""
    
    def __init__(self):
        super().__init__(
            rule_id="R002",
            name="共享地址检测",
            description="检测多个高风险账户共享同一地址的情况，可能是欺诈团伙",
            risk_level=7
        )
    
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """评估是否存在共享地址
        
        Args:
            context: 包含知识图谱和账户信息的上下文
            
        Returns:
            评估结果
        """
        kg = context.get('knowledge_graph')
        account_id = context.get('account_id')
        
        if not kg or not account_id:
            return {
                'rule_id': self.rule_id,
                'triggered': False,
                'risk_level': 0,
                'details': "缺少必要的评估信息"
            }
        
        # 查找账户关联的地址
        addresses = []
        for _, target, data in kg.graph.out_edges(account_id, data=True):
            if data.get('relation_type') == 'has_address':
                addresses.append(target)
        
        if not addresses:
            return