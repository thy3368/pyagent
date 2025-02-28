from openai import OpenAI
import os
import argparse
import xml.etree.ElementTree as ET
import json

class Text2HDDMLAgent:
    def __init__(self):
        """初始化 Text2HDDML 转换代理"""
        self.client = OpenAI(
            api_key="sk-XvWvy8rf8ewno0vVFmtgOMidGb5i3h1qNQmer7bE2buY6hlK",
            base_url="https://tbnx.plus7.plus/v1"
        )
        
    def generate_hddml(self, description: str) -> str:
        """将自然语言描述转换为 HDDML"""
        prompt = f"""请将以下数据结构描述转换为 HDDML (Hierarchical Data Definition Markup Language) 格式：

{description}

HDDML 是一种用于定义层次化数据结构的标记语言，类似于 XML 但专注于数据定义。
请确保生成的 HDDML 包含所有必要的元素、属性和层次关系。
只需返回 HDDML 内容，不要包含任何其他解释。

示例 HDDML 格式：
<hddml version="1.0">
  <entity name="User">
    <attribute name="id" type="integer" primary="true"/>
    <attribute name="name" type="string" length="100"/>
    <attribute name="email" type="string" length="255"/>
    <relationship name="orders" type="one-to-many" target="Order"/>
  </entity>
</hddml>"""

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        hddml_content = response.choices[0].message.content
        
        # 尝试提取 HDDML 部分
        if "```" in hddml_content:
            hddml_content = hddml_content.split("```")[1].split("```")[0].strip()
            if hddml_content.startswith("xml") or hddml_content.startswith("hddml"):
                hddml_content = hddml_content.split("\n", 1)[1]
                
        return hddml_content
    
    def validate_hddml(self, hddml_string: str) -> bool:
        """验证 HDDML 格式是否有效"""
        try:
            ET.fromstring(hddml_string)
            return True
        except ET.ParseError:
            return False
    
    def save_hddml(self, hddml_content: str, output_path: str) -> bool:
        """保存 HDDML 到文件"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(hddml_content)
            return True
        except Exception as e:
            print(f"保存 HDDML 文件失败: {e}")
            return False
            
    def convert_to_json_schema(self, hddml_content: str) -> dict:
        """将 HDDML 转换为 JSON Schema"""
        try:
            root = ET.fromstring(hddml_content)
            schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "definitions": {}
            }
            
            for entity in root.findall(".//entity"):
                entity_name = entity.get("name")
                entity_schema = {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
                
                for attr in entity.findall("./attribute"):
                    attr_name = attr.get("name")
                    attr_type = attr.get("type")
                    
                    # 类型映射
                    json_type = "string"
                    if attr_type == "integer":
                        json_type = "integer"
                    elif attr_type == "number" or attr_type == "float":
                        json_type = "number"
                    elif attr_type == "boolean":
                        json_type = "boolean"
                    
                    attr_schema = {"type": json_type}
                    
                    # 添加其他属性
                    if attr.get("length"):
                        attr_schema["maxLength"] = int(attr.get("length"))
                    
                    if attr.get("required") == "true":
                        entity_schema["required"].append(attr_name)
                        
                    entity_schema["properties"][attr_name] = attr_schema
                
                schema["definitions"][entity_name] = entity_schema
                
                # 如果是根实体，设置为主模式
                if entity.get("root") == "true":
                    schema["$ref"] = f"#/definitions/{entity_name}"
            
            return schema
        except Exception as e:
            print(f"转换为 JSON Schema 失败: {e}")
            return {}

def main():
    parser = argparse.ArgumentParser(description='将自然语言描述转换为 HDDML')
    parser.add_argument('--text', type=str, help='直接输入文本描述')
    parser.add_argument('--input', type=str, help='输入描述文件路径')
    parser.add_argument('--output', type=str, default='/Users/hongyaotang/src/py/pyagent/output/generated.hddml', 
                        help='输出 HDDML 文件路径')
    parser.add_argument('--json', action='store_true', help='同时生成 JSON Schema')
    parser.add_argument('--interactive', action='store_true', help='交互模式')
    
    args = parser.parse_args()
    
    agent = Text2HDDMLAgent()
    
    # 处理直接输入的文本
    if args.text:
        print("正在生成 HDDML...")
        hddml_content = agent.generate_hddml(args.text)
        
        is_valid = agent.validate_hddml(hddml_content)
        print(f"HDDML 格式{'有效' if is_valid else '无效'}")
        
        output_path = args.output
        if agent.save_hddml(hddml_content, output_path):
            print(f"HDDML 已保存到: {output_path}")
            
            if args.json and is_valid:
                json_schema = agent.convert_to_json_schema(hddml_content)
                json_path = output_path.replace('.hddml', '.json')
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(json_schema, f, indent=2)
                print(f"JSON Schema 已保存到: {json_path}")
        return
    
    if args.interactive:
        print("自然语言到 HDDML 转换助手已启动")
        print("输入 'exit' 退出程序")
        
        while True:
            description = input("\n请输入数据结构描述: ")
            if description.lower() == 'exit':
                print("再见！")
                break
                
            print("正在生成 HDDML...")
            hddml_content = agent.generate_hddml(description)
            
            is_valid = agent.validate_hddml(hddml_content)
            print(f"HDDML 格式{'有效' if is_valid else '无效'}")
            
            print("\n生成的 HDDML:")
            print("----------------------------------------")
            print(hddml_content)
            print("----------------------------------------")
            
            save = input("\n是否保存? (y/n): ")
            if save.lower() == 'y':
                save_path = input("请输入保存路径 (直接回车使用默认路径): ")
                if not save_path:
                    save_path = args.output
                
                if agent.save_hddml(hddml_content, save_path):
                    print(f"HDDML 已保存到: {save_path}")
                    
                    if args.json and is_valid:
                        json_schema = agent.convert_to_json_schema(hddml_content)
                        json_path = save_path.replace('.hddml', '.json')
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(json_schema, f, indent=2)
                        print(f"JSON Schema 已保存到: {json_path}")
    else:
        if not args.input:
            print("错误: 请提供输入文件路径、直接输入文本或使用交互模式")
            return
            
        with open(args.input, 'r', encoding='utf-8') as f:
            description = f.read()
            
        print("正在生成 HDDML...")
        hddml_content = agent.generate_hddml(description)
        
        is_valid = agent.validate_hddml(hddml_content)
        print(f"HDDML 格式{'有效' if is_valid else '无效'}")
        
        if agent.save_hddml(hddml_content, args.output):
            print(f"HDDML 已保存到: {args.output}")
            
            if args.json and is_valid:
                json_schema = agent.convert_to_json_schema(hddml_content)
                json_path = args.output.replace('.hddml', '.json')
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(json_schema, f, indent=2)
                print(f"JSON Schema 已保存到: {json_path}")

if __name__ == "__main__":
    main()