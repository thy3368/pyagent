import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import json
import os
from typing import Dict, List, Any, Tuple, Set
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("KG_Risk_Control")

class FinancialKnowledgeGraph:
    """金融知识图谱类"""
    
    def __init__(self):
        """初始化金融知识图谱"""
        self.graph = nx.DiGraph()
        self.entity_types = set()
        self.relation_types = set()
    
    def add_entity(self, entity_id: str, entity_type: str, attributes: Dict = None):
        """添加实体到图谱
        
        Args:
            entity_id: 实体ID
            entity_type: 实体类型
            attributes: 实体属性
        """
        if attributes is None:
            attributes = {}
            
        attributes['entity_type'] = entity_type
        self.entity_types.add(entity_type)
        
        self.graph.add_node(entity_id, **attributes)
        logger.debug(f"添加实体: {entity_id}, 类型: {entity_type}")
    
    def add_relation(self, source_id: str, target_id: str, relation_type: str, attributes: Dict = None):
        """添加关系到图谱
        
        Args:
            source_id: 源实体ID
            target_id: 目标实体ID
            relation_type: 关系类型
            attributes: 关系属性
        """
        if attributes is None:
            attributes = {}
            
        attributes['relation_type'] = relation_type
        self.relation_types.add(relation_type)
        
        self.graph.add_edge(source_id, target_id, **attributes)
        logger.debug(f"添加关系: {source_id} --[{relation_type}]--> {target_id}")
    
    def get_entity(self, entity_id: str) -> Dict:
        """获取实体信息
        
        Args:
            entity_id: 实体ID
            
        Returns:
            实体信息
        """
        if entity_id in self.graph.nodes:
            return dict(self.graph.nodes[entity_id])
        return None
    
    def get_relations(self, entity_id: str, direction: str = 'out') -> List[Tuple]:
        """获取实体的关系
        
        Args:
            entity_id: 实体ID
            direction: 关系方向，'out'表示出边，'in'表示入边，'both'表示双向
            
        Returns:
            关系列表
        """
        relations = []
        
        if direction in ['out', 'both']:
            for _, target_id, data in self.graph.out_edges(entity_id, data=True):
                relations.append(('out', target_id, data))
                
        if direction in ['in', 'both']:
            for source_id, _, data in self.graph.in_edges(entity_id, data=True):
                relations.append(('in', source_id, data))
                
        return relations
    
    def find_path(self, source_id: str, target_id: str, max_depth: int = 3) -> List[List[Tuple]]:
        """查找两个实体之间的路径
        
        Args:
            source_id: 源实体ID
            target_id: 目标实体ID
            max_depth: 最大深度
            
        Returns:
            路径列表
        """
        try:
            paths = list(nx.all_simple_paths(self.graph, source_id, target_id, cutoff=max_depth))
            result = []
            
            for path in paths:
                path_with_relations = []
                for i in range(len(path) - 1):
                    source = path[i]
                    target = path[i + 1]
                    edge_data = self.graph.get_edge_data(source, target)
                    path_with_relations.append((source, target, edge_data))
                result.append(path_with_relations)
                
            return result
        except nx.NetworkXNoPath:
            return []
    
    def find_common_neighbors(self, entity_ids: List[str]) -> Dict[str, Set[str]]:
        """查找多个实体的共同邻居
        
        Args:
            entity_ids: 实体ID列表
            
        Returns:
            共同邻居字典
        """
        if not entity_ids:
            return {}
            
        neighbors = {}
        for entity_id in entity_ids:
            neighbors[entity_id] = set(self.graph.successors(entity_id)) | set(self.graph.predecessors(entity_id))
            
        common = set.intersection(*neighbors.values()) if neighbors else set()
        return {entity_id: common for entity_id in entity_ids}
    
    def get_subgraph(self, entity_ids: List[str], depth: int = 1) -> 'FinancialKnowledgeGraph':
        """获取以指定实体为中心的子图
        
        Args:
            entity_ids: 实体ID列表
            depth: 扩展深度
            
        Returns:
            子图
        """
        nodes_to_include = set(entity_ids)
        frontier = set(entity_ids)
        
        for _ in range(depth):
            new_frontier = set()
            for node in frontier:
                new_frontier.update(self.graph.successors(node))
                new_frontier.update(self.graph.predecessors(node))
            frontier = new_frontier - nodes_to_include
            nodes_to_include.update(frontier)
        
        subgraph = self.graph.subgraph(nodes_to_include)
        
        result = FinancialKnowledgeGraph()
        result.graph = subgraph
        result.entity_types = self.entity_types
        result.relation_types = self.relation_types
        
        return result
    
    def visualize(self, output_path: str = None, figsize: Tuple[int, int] = (12, 10)):
        """可视化知识图谱
        
        Args:
            output_path: 输出文件路径
            figsize: 图像大小
        """
        plt.figure(figsize=figsize)
        
        # 设置节点颜色映射
        entity_types = list(self.entity_types)
        color_map = {}
        for i, entity_type in enumerate(entity_types):
            color_map[entity_type] = plt.cm.tab10(i / len(entity_types))
        
        # 获取节点颜色
        node_colors = []
        for node in self.graph.nodes():
            entity_type = self.graph.nodes[node].get('entity_type', 'unknown')
            node_colors.append(color_map.get(entity_type, 'gray'))
        
        # 绘制图形
        pos = nx.spring_layout(self.graph, seed=42)
        nx.draw_networkx_nodes(self.graph, pos, node_color=node_colors, alpha=0.8, node_size=500)
        nx.draw_networkx_edges(self.graph, pos, alpha=0.5, arrows=True)
        nx.draw_networkx_labels(self.graph, pos, font_size=10)
        
        # 添加图例
        legend_elements = []
        for entity_type, color in color_map.items():
            legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
                                             markerfacecolor=color, markersize=10, label=entity_type))
        plt.legend(handles=legend_elements, loc='upper right')
        
        plt.axis('off')
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            logger.info(f"图谱已保存到: {output_path}")
        else:
            plt.show()
        
        plt.close()
    
    def save(self, file_path: str):
        """保存知识图谱到文件
        
        Args:
            file_path: 文件路径
        """
        data = {
            'nodes': [],
            'edges': [],
            'entity_types': list(self.entity_types),
            'relation_types': list(self.relation_types)
        }
        
        for node, attrs in self.graph.nodes(data=True):
            node_data = {'id': node}
            node_data.update(attrs)
            data['nodes'].append(node_data)
        
        for source, target, attrs in self.graph.edges(data=True):
            edge_data = {'source': source, 'target': target}
            edge_data.update(attrs)
            data['edges'].append(edge_data)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"知识图谱已保存到: {file_path}")
    
    @classmethod
    def load(cls, file_path: str) -> 'FinancialKnowledgeGraph':
        """从文件加载知识图谱
        
        Args:
            file_path: 文件路径
            
        Returns:
            知识图谱对象
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        kg = cls()
        kg.entity_types = set(data.get('entity_types', []))
        kg.relation_types = set(data.get('relation_types', []))
        
        for node in data.get('nodes', []):
            node_id = node.pop('id')
            entity_type = node.pop('entity_type', 'unknown')
            kg.add_entity(node_id, entity_type, node)
        
        for edge in data.get('edges', []):
            source = edge.pop('source')
            target = edge.pop('target')
            relation_type = edge.pop('relation_type', 'unknown')
            kg.add_relation(source, target, relation_type, edge)
        
        logger.info(f"已从{file_path}加载知识图谱")
        return kg