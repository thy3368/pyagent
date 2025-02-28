from transformers import AutoTokenizer, AutoModelForCausalLM, ViTFeatureExtractor
import networkx as nx
import torch
from PIL import Image
import json
import base64

class KGMultiModalReasoner:
    def __init__(self):
        # 初始化模型和处理器
        self.model_name = "deepseek-ai/deepseek-coder-6.7b-base"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.image_processor = ViTFeatureExtractor.from_pretrained("google/vit-base-patch16-224")
        
        # 初始化知识图谱
        self.kg = nx.DiGraph()
        self.load_knowledge_base()
        
    def load_knowledge_base(self):
        """加载知识图谱数据"""
        # 示例知识图谱数据
        entities = [
            {"id": "person1", "type": "Person", "name": "张三"},
            {"id": "person2", "type": "Person", "name": "李四"},
            {"id": "location1", "type": "Location", "name": "北京"},
        ]
        
        relations = [
            {"from": "person1", "to": "location1", "type": "lives_in"},
            {"from": "person2", "to": "location1", "type": "visited"},
        ]
        
        # 构建图谱
        for entity in entities:
            self.kg.add_node(entity["id"], **entity)
        
        for relation in relations:
            self.kg.add_edge(
                relation["from"],
                relation["to"],
                type=relation["type"]
            )
    
    def process_image(self, image_path: str) -> dict:
        """处理图片输入"""
        try:
            image = Image.open(image_path).convert('RGB')
            image_features = self.image_processor(image, return_tensors="pt")
            
            # 这里可以添加图像识别的逻辑
            # 返回识别到的实体和关系
            return {
                "entities": ["detected_object_1", "detected_object_2"],
                "relations": ["relation_1"]
            }
        except Exception as e:
            return {"error": f"图片处理错误：{str(e)}"}
    
    def query_knowledge_graph(self, query: dict) -> list:
        """查询知识图谱"""
        results = []
        
        # 根据查询条件在图谱中搜索
        if "entity" in query:
            entity = query["entity"]
            if entity in self.kg.nodes:
                node_data = self.kg.nodes[entity]
                results.append({
                    "type": "entity",
                    "data": node_data
                })
                
                # 获取相关关系
                for _, neighbor, edge_data in self.kg.edges(entity, data=True):
                    results.append({
                        "type": "relation",
                        "from": entity,
                        "to": neighbor,
                        "relation": edge_data["type"]
                    })
        
        return results
    
    def reason(self, query: str, image_path: str = None) -> str:
        """多模态推理"""
        context = {"text_query": query}
        
        # 处理图片输入
        if image_path:
            image_info = self.process_image(image_path)
            context["image_info"] = image_info
        
        # 在知识图谱中查询相关信息
        kg_results = self.query_knowledge_graph({"entity": "person1"})  # 示例查询
        context["kg_info"] = kg_results
        
        # 构建推理提示
        prompt = f"""基于以下信息进行推理：

1. 用户查询：{query}

2. 知识图谱信息：
{json.dumps(kg_results, ensure_ascii=False, indent=2)}

3. 图片信息（如果有）：
{json.dumps(context.get('image_info', {}), ensure_ascii=False, indent=2)}

请提供推理结果："""

        # 生成推理结果
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(
            inputs["input_ids"],
            max_length=512,
            num_return_sequences=1,
            temperature=0.7
        )
        
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

def main():
    # 创建推理器实例
    reasoner = KGMultiModalReasoner()
    
    print("多模态知识图谱推理系统已启动")
    print("支持的命令：")
    print("1. 'image:路径 查询文本' - 基于图片和文本的推理")
    print("2. 直接输入文本 - 基于文本的推理")
    print("输入 '退出' 结束程序")
    
    while True:
        user_input = input("\n请输入查询: ")
        if user_input.lower() == "退出":
            print("再见！")
            break
        
        if user_input.startswith("image:"):
            # 解析图片路径和查询文本
            parts = user_input.split(" ", 1)
            image_path = parts[0][6:]
            query = parts[1] if len(parts) > 1 else ""
            result = reasoner.reason(query, image_path)
        else:
            result = reasoner.reason(user_input)
        
        print("\n推理结果：")
        print("----------------------------------------")
        print(result)
        print("----------------------------------------")

if __name__ == "__main__":
    main()