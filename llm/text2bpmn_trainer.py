from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments
from datasets import Dataset
import torch
import os
import json
import xml.etree.ElementTree as ET

def prepare_data(data_dir: str):
    """准备训练数据：自然语言描述和对应的 BPMN XML"""
    text_inputs = []
    bpmn_outputs = []
    
    # 数据目录结构：
    # data_dir/
    #   ├── descriptions/
    #   │   ├── process1.txt
    #   │   └── process2.txt
    #   └── bpmn/
    #       ├── process1.bpmn
    #       └── process2.bpmn
    
    descriptions_dir = os.path.join(data_dir, "descriptions")
    bpmn_dir = os.path.join(data_dir, "bpmn")
    
    for desc_file in os.listdir(descriptions_dir):
        if desc_file.endswith('.txt'):
            # 获取对应的 BPMN 文件
            bpmn_file = os.path.join(bpmn_dir, desc_file.replace('.txt', '.bpmn'))
            if os.path.exists(bpmn_file):
                with open(os.path.join(descriptions_dir, desc_file), 'r', encoding='utf-8') as f:
                    text_inputs.append(f.read().strip())
                with open(bpmn_file, 'r', encoding='utf-8') as f:
                    bpmn_outputs.append(f.read().strip())
    
    return Dataset.from_dict({
        "description": text_inputs,
        "bpmn": bpmn_outputs
    })

def format_training_example(description: str, bpmn: str) -> str:
    """格式化训练样本"""
    return f"""### 业务流程描述
{description}

### BPMN XML
{bpmn}

### 结束"""

def main():
    # 加载模型和分词器
    model_name = "deepseek-ai/deepseek-coder-6.7b-base"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    
    # 准备数据
    dataset = prepare_data("/Users/hongyaotang/src/py/pyagent/data/text2bpmn")
    
    def preprocess_function(examples):
        # 将输入和输出组合成训练格式
        formatted_data = [
            format_training_example(desc, bpmn)
            for desc, bpmn in zip(examples["description"], examples["bpmn"])
        ]
        
        # 转换为模型输入
        return tokenizer(
            formatted_data,
            padding="max_length",
            truncation=True,
            max_length=1024,  # BPMN XML 可能较长
            return_tensors="pt"
        )
    
    processed_dataset = dataset.map(
        preprocess_function,
        batched=True,
        remove_columns=dataset.column_names
    )
    
    # 训练参数
    training_args = TrainingArguments(
        output_dir="/Users/hongyaotang/src/py/pyagent/models/text2bpmn_output",
        num_train_epochs=5,
        per_device_train_batch_size=2,  # 较小的批量大小以适应长序列
        save_steps=100,
        save_total_limit=2,
        learning_rate=1e-5,
        gradient_accumulation_steps=8,
        fp16=True,
    )
    
    # 初始化训练器
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=processed_dataset,
    )
    
    # 开始训练
    trainer.train()
    
    # 保存模型
    trainer.save_model("/Users/hongyaotang/src/py/pyagent/models/text2bpmn_trained_model")
    
    # 测试生成
    def generate_bpmn(description: str, max_length=2048):
        prompt = f"### 业务流程描述\n{description}\n\n### BPMN XML\n"
        inputs = tokenizer(prompt, return_tensors="pt")
        
        outputs = model.generate(
            inputs["input_ids"],
            max_length=max_length,
            num_return_sequences=1,
            no_repeat_ngram_size=0,  # XML 可能有重复模式
            temperature=0.3  # 较低的温度以保证结构正确性
        )
        
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # 提取生成的 BPMN XML
        try:
            return generated_text.split("### BPMN XML\n")[1].split("### 结束")[0].strip()
        except:
            return generated_text
    
    # 测试生成效果
    test_descriptions = [
        "一个简单的订单处理流程：客户提交订单后，系统进行库存检查。如果库存充足，则进行支付处理；否则通知客户缺货。支付成功后，系统安排发货并通知客户。",
        "员工请假流程：员工提交请假申请，直接主管审批。如果请假天数超过3天，还需部门经理审批。所有审批通过后，人力资源部门备案。"
    ]
    
    print("\n测试生成：")
    for desc in test_descriptions:
        print(f"\n输入描述: {desc[:50]}...")
        bpmn_xml = generate_bpmn(desc)
        print(f"生成的 BPMN XML (前200字符):")
        print(bpmn_xml[:200] + "...")
        
        # 验证 XML 有效性
        try:
            ET.fromstring(bpmn_xml)
            print("XML 格式有效")
        except ET.ParseError as e:
            print(f"XML 格式无效: {e}")

if __name__ == "__main__":
    main()