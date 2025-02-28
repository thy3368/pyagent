from transformers import AutoTokenizer, AutoModelForCausalLM
from datasets import Dataset
import torch
from torch.utils.data import DataLoader
from transformers import TrainingArguments, Trainer

def prepare_data():
    # 准备训练数据
    training_data = [
        "机器学习是人工智能的一个重要分支。",
        "深度学习是机器学习中的一种方法。",
        "神经网络是深度学习的基础。",
        "人工智能正在改变我们的生活方式。",
        "数据是机器学习中最重要的资源。"
    ]
    
    return Dataset.from_dict({"text": training_data})

def main():
    # 加载模型和分词器
    model_name = "deepseek-ai/deepseek-coder-6.7b-base"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    
    # 准备数据
    dataset = prepare_data()
    
    def tokenize_function(examples):
        return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=128)
    
    tokenized_dataset = dataset.map(tokenize_function, batched=True)
    
    # 训练参数
    training_args = TrainingArguments(
        output_dir="./deepseek_output",
        num_train_epochs=3,
        per_device_train_batch_size=4,
        save_steps=500,
        save_total_limit=2,
        learning_rate=2e-5,
    )
    
    # 初始化训练器
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
    )
    
    # 开始训练
    trainer.train()
    
    # 保存模型
    trainer.save_model("./deepseek_trained_model")
    
    # 测试生成
    def generate_text(prompt, max_length=50):
        inputs = tokenizer(prompt, return_tensors="pt")
        outputs = model.generate(
            inputs["input_ids"],
            max_length=max_length,
            num_return_sequences=1,
            no_repeat_ngram_size=2,
            temperature=0.7
        )
        return tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # 测试一些生成效果
    test_prompts = [
        "机器学习的应用领域包括",
        "深度学习主要解决",
        "人工智能的未来发展"
    ]
    
    print("\n生成测试：")
    for prompt in test_prompts:
        generated = generate_text(prompt)
        print(f"\n输入: {prompt}")
        print(f"输出: {generated}")

if __name__ == "__main__":
    main()