from transformers import AutoTokenizer, AutoModelForCausalLM
import xml.etree.ElementTree as ET
import os
import argparse

class Text2BPMNAgent:
    def __init__(self, model_path="/Users/hongyaotang/src/py/pyagent/models/text2bpmn_trained_model"):
        """初始化 Text2BPMN 转换代理"""
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(model_path)
        
    def generate_bpmn(self, description: str, max_length=2048) -> str:
        """将自然语言描述转换为 BPMN XML"""
        prompt = f"### 业务流程描述\n{description}\n\n### BPMN XML\n"
        inputs = self.tokenizer(prompt, return_tensors="pt")
        
        outputs = self.model.generate(
            inputs["input_ids"],
            max_length=max_length,
            num_return_sequences=1,
            no_repeat_ngram_size=0,
            temperature=0.3
        )
        
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # 提取生成的 BPMN XML
        try:
            bpmn_xml = generated_text.split("### BPMN XML\n")[1].split("### 结束")[0].strip()
            return bpmn_xml
        except:
            return generated_text
    
    def validate_xml(self, xml_string: str) -> bool:
        """验证 XML 格式是否有效"""
        try:
            ET.fromstring(xml_string)
            return True
        except ET.ParseError:
            return False
    
    def save_bpmn(self, bpmn_xml: str, output_path: str) -> bool:
        """保存 BPMN 到文件"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(bpmn_xml)
            return True
        except Exception as e:
            print(f"保存 BPMN 文件失败: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='将自然语言描述转换为 BPMN')
    parser.add_argument('--input', type=str, help='输入描述文件路径')
    parser.add_argument('--output', type=str, default='/Users/hongyaotang/src/py/pyagent/output/generated.bpmn', 
                        help='输出 BPMN 文件路径')
    parser.add_argument('--interactive', action='store_true', help='交互模式')
    
    args = parser.parse_args()
    
    agent = Text2BPMNAgent()
    
    if args.interactive:
        print("自然语言到 BPMN 转换助手已启动")
        print("输入 'exit' 退出程序")
        
        while True:
            description = input("\n请输入业务流程描述: ")
            if description.lower() == 'exit':
                print("再见！")
                break
                
            print("正在生成 BPMN...")
            bpmn_xml = agent.generate_bpmn(description)
            
            is_valid = agent.validate_xml(bpmn_xml)
            print(f"XML 格式{'有效' if is_valid else '无效'}")
            
            if is_valid:
                save_path = input("请输入保存路径 (直接回车使用默认路径): ")
                if not save_path:
                    save_path = args.output
                
                if agent.save_bpmn(bpmn_xml, save_path):
                    print(f"BPMN 已保存到: {save_path}")
    else:
        if not args.input:
            print("错误: 请提供输入文件路径或使用交互模式")
            return
            
        with open(args.input, 'r', encoding='utf-8') as f:
            description = f.read()
            
        print("正在生成 BPMN...")
        bpmn_xml = agent.generate_bpmn(description)
        
        is_valid = agent.validate_xml(bpmn_xml)
        print(f"XML 格式{'有效' if is_valid else '无效'}")
        
        if is_valid and agent.save_bpmn(bpmn_xml, args.output):
            print(f"BPMN 已保存到: {args.output}")

if __name__ == "__main__":
    main()