import networkx as nx
import json
from typing import List, Dict, Any
from openai import OpenAI

class MedicalKG:
    def __init__(self):
        self.kg = nx.DiGraph()
        self.client = OpenAI(
            api_key="sk-XvWvy8rf8ewno0vVFmtgOMidGb5i3h1qNQmer7bE2buY6hlK",
            base_url="https://tbnx.plus7.plus/v1"
        )
        self.load_knowledge_base()

    def load_knowledge_base(self):
        """加载医疗知识图谱"""
        # 示例数据：疾病、症状、药品
        diseases = [
            {"id": "d1", "type": "Disease", "name": "感冒", "description": "常见呼吸道感染"},
            {"id": "d2", "type": "Disease", "name": "高血压", "description": "血压持续升高"},
        ]
        
        symptoms = [
            {"id": "s1", "type": "Symptom", "name": "发热"},
            {"id": "s2", "type": "Symptom", "name": "咳嗽"},
            {"id": "s3", "type": "Symptom", "name": "头痛"},
            {"id": "s4", "type": "Symptom", "name": "头晕"},
        ]
        
        medicines = [
            {"id": "m1", "type": "Medicine", "name": "布洛芬", "usage": "退热镇痛"},
            {"id": "m2", "type": "Medicine", "name": "感冒灵", "usage": "感冒症状"},
            {"id": "m3", "type": "Medicine", "name": "降压药", "usage": "降血压"},
        ]
        
        # 添加实体
        for entity in diseases + symptoms + medicines:
            self.kg.add_node(entity["id"], **entity)
        
        # 添加关系
        relations = [
            {"from": "d1", "to": "s1", "type": "has_symptom"},
            {"from": "d1", "to": "s2", "type": "has_symptom"},
            {"from": "d2", "to": "s4", "type": "has_symptom"},
            {"from": "m1", "to": "s1", "type": "treats"},
            {"from": "m2", "to": "d1", "type": "treats"},
            {"from": "m3", "to": "d2", "type": "treats"},
        ]
        
        for relation in relations:
            self.kg.add_edge(relation["from"], relation["to"], type=relation["type"])

    def diagnose(self, symptoms: List[str]) -> List[Dict[str, Any]]:
        """根据症状进行诊断"""
        results = []
        symptom_nodes = [
            node for node in self.kg.nodes(data=True)
            if node[1]["type"] == "Symptom" and node[1]["name"] in symptoms
        ]
        
        for symptom_id, _ in symptom_nodes:
            # 查找与症状相关的疾病
            for pred in self.kg.predecessors(symptom_id):
                node_data = self.kg.nodes[pred]
                if node_data["type"] == "Disease":
                    results.append({
                        "disease": node_data["name"],
                        "description": node_data["description"],
                        "symptom": self.kg.nodes[symptom_id]["name"]
                    })
        
        return results

    def recommend_medicine(self, disease: str) -> List[Dict[str, Any]]:
        """推荐用药"""
        results = []
        disease_nodes = [
            node for node in self.kg.nodes(data=True)
            if node[1]["type"] == "Disease" and node[1]["name"] == disease
        ]
        
        for disease_id, _ in disease_nodes:
            # 查找治疗该疾病的药品
            for pred in self.kg.predecessors(disease_id):
                node_data = self.kg.nodes[pred]
                if node_data["type"] == "Medicine":
                    results.append({
                        "medicine": node_data["name"],
                        "usage": node_data["usage"]
                    })
        
        return results

    def get_ai_suggestion(self, diagnosis_results: List[Dict], medicine_results: List[Dict]) -> str:
        """获取 AI 建议"""
        context = {
            "diagnosis": diagnosis_results,
            "medicines": medicine_results
        }
        
        prompt = f"""基于以下诊断和用药信息提供建议：

诊断结果：
{json.dumps(diagnosis_results, ensure_ascii=False, indent=2)}

推荐用药：
{json.dumps(medicine_results, ensure_ascii=False, indent=2)}

请提供专业的建议："""

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        return response.choices[0].message.content

def main():
    kg = MedicalKG()
    print("医疗知识图谱系统已启动")
    print("支持的功能：")
    print("1. 症状诊断")
    print("2. 用药推荐")
    print("输入 '退出' 结束程序")
    
    while True:
        print("\n请选择功能：")
        print("1. 输入症状进行诊断")
        print("2. 输入疾病获取用药建议")
        choice = input("请选择 (1/2): ")
        
        if choice == "退出":
            print("再见！")
            break
        
        if choice == "1":
            symptoms = input("请输入症状（多个症状用逗号分隔）: ").split(",")
            diagnosis_results = kg.diagnose([s.strip() for s in symptoms])
            
            if diagnosis_results:
                print("\n可能的疾病：")
                for result in diagnosis_results:
                    print(f"- {result['disease']}: {result['description']}")
                    
                # 获取用药建议
                all_medicines = []
                for result in diagnosis_results:
                    medicines = kg.recommend_medicine(result['disease'])
                    all_medicines.extend(medicines)
                
                if all_medicines:
                    print("\nAI 建议：")
                    suggestion = kg.get_ai_suggestion(diagnosis_results, all_medicines)
                    print(suggestion)
            else:
                print("未找到相关诊断信息")
                
        elif choice == "2":
            disease = input("请输入疾病名称: ")
            medicine_results = kg.recommend_medicine(disease)
            
            if medicine_results:
                print("\n推荐用药：")
                for result in medicine_results:
                    print(f"- {result['medicine']}: {result['usage']}")
                
                suggestion = kg.get_ai_suggestion([], medicine_results)
                print("\nAI 建议：")
                print(suggestion)
            else:
                print("未找到相关用药信息")

if __name__ == "__main__":
    main()