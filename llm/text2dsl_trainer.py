from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments
from datasets import Dataset
import torch
import os

def prepare_data(data_dir: str):
    """准备训练数据：自然语言和对应的 DSL 代码对"""
    text_inputs = []
    dsl_outputs = []
    
    # 数据目录结构：
    # data_dir/
    #   ├── inputs/
    #   │   ├── query1.txt
    #   │   └── query2.txt
    #   └── outputs/
    #       ├── dsl1.sql
    #       └── dsl2.sql
    
    inputs_dir = os.path.join(data_dir, "inputs")
    outputs_dir = os.path.join(data_dir, "outputs")
    
    for input_file in os.listdir(inputs_dir):
        if input_file.endswith('.txt'):
            # 获取对应的 DSL 文件
            dsl_file = os.path.join(outputs_dir, input_file.replace('.txt', '.sql'))
            if os.path.exists(dsl_file):
                with open(os.path.join(inputs_dir, input_file), 'r') as f:
                    text_inputs.append(f.read().strip())
                with open(dsl_file, 'r') as f:
                    dsl_outputs.append(f.read().strip())
    
    return Dataset.from_dict({
        "text": text_inputs,
        "dsl": dsl_outputs
    })

def format_training_example(text: str, dsl: str) -> str:
    """格式化训练样本"""
    return f"""### 输入
{text}

### 输出
{dsl}

### 结束"""

def main():
    # 加载模型和分词器
    model_name = "deepseek-ai/deepseek-coder-6.7b-base"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    
    # 准备数据
    dataset = prepare_data("/Users/hongyaotang/src/py/pyagent/data/text2dsl")
    
    def preprocess_function(examples):
        # 将输入和输出组合成训练格式
        formatted_data = [
            format_training_example(text, dsl)
            for text, dsl in zip(examples["text"], examples["dsl"])
        ]
        
        # 转换为模型输入
        return tokenizer(
            formatted_data,
            padding="max_length",
            truncation=True,
            max_length=512,
            return_tensors="pt"
        )
    
    processed_dataset = dataset.map(
        preprocess_function,
        batched=True,
        remove_columns=dataset.column_names
    )
    
    # 训练参数
    training_args = TrainingArguments(
        output_dir="./text2dsl_output",
        num_train_epochs=3,
        per_device_train_batch_size=4,
        save_steps=100,
        save_total_limit=2,
        learning_rate=2e-5,
        gradient_accumulation_steps=4,
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
    trainer.save_model("./text2dsl_trained_model")
    
    # 测试生成
    def generate_dsl(text: str, max_length=512):
        prompt = f"### 输入\n{text}\n\n### 输出\n"
        inputs = tokenizer(prompt, return_tensors="pt")
        
        outputs = model.generate(
            inputs["input_ids"],
            max_length=max_length,
            num_return_sequences=1,
            no_repeat_ngram_size=2,
            temperature=0.7
        )
        
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        # 提取生成的 DSL 代码
        try:
            return generated_text.split("### 输出\n")[1].split("### 结束")[0].strip()
        except:
            return generated_text
    
    # 测试生成效果
    test_queries = [
        "查询所有用户的订单总数",
        "统计最近7天的销售额",
        "找出购买金额最高的前10个客户"
    ]
    
    print("\n测试生成：")
    for query in test_queries:
        print(f"\n输入: {query}")
        print(f"生成的 DSL:")
        print(generate_dsl(query))

if __name__ == "__main__":
    main()