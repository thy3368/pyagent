from transformers import AutoTokenizer, AutoModelForCausalLM, VisionEncoderDecoderModel
from transformers import ViTFeatureExtractor
from datasets import Dataset
import torch
from torch.utils.data import DataLoader
from transformers import TrainingArguments, Trainer
from PIL import Image
import os

def prepare_data(data_dir: str):
    """准备训练数据：图片路径和对应的 Vue 代码"""
    image_paths = []
    vue_codes = []
    
    # 示例数据结构：
    # data_dir/
    #   ├── images/
    #   │   ├── img1.jpg
    #   │   └── img2.jpg
    #   └── codes/
    #       ├── code1.vue
    #       └── code2.vue
    
    images_dir = os.path.join(data_dir, "images")
    codes_dir = os.path.join(data_dir, "codes")
    
    for img_file in os.listdir(images_dir):
        if img_file.endswith(('.jpg', '.png')):
            # 获取对应的代码文件
            code_file = os.path.join(codes_dir, img_file.rsplit('.', 1)[0] + '.vue')
            if os.path.exists(code_file):
                image_paths.append(os.path.join(images_dir, img_file))
                with open(code_file, 'r') as f:
                    vue_codes.append(f.read())
    
    return Dataset.from_dict({
        "image_path": image_paths,
        "vue_code": vue_codes
    })

def main():
    # 加载模型和处理器
    model_name = "deepseek-ai/deepseek-coder-6.7b-base"
    image_processor = ViTFeatureExtractor.from_pretrained("google/vit-base-patch16-224")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    # 初始化多模态模型
    model = VisionEncoderDecoderModel.from_encoder_decoder_pretrained(
        "google/vit-base-patch16-224",
        model_name
    )
    
    # 准备数据
    dataset = prepare_data("/Users/hongyaotang/src/py/pyagent/data/image2vue")
    
    def preprocess_function(examples):
        # 处理图片
        images = [Image.open(path).convert('RGB') for path in examples["image_path"]]
        image_features = image_processor(images, return_tensors="pt")["pixel_values"]
        
        # 处理代码文本
        text_features = tokenizer(
            examples["vue_code"],
            padding="max_length",
            truncation=True,
            max_length=512,
            return_tensors="pt"
        )
        
        return {
            "pixel_values": image_features,
            "labels": text_features["input_ids"]
        }
    
    processed_dataset = dataset.map(
        preprocess_function,
        batched=True,
        remove_columns=dataset.column_names
    )
    
    # 训练参数
    training_args = TrainingArguments(
        output_dir="./image2vue_output",
        num_train_epochs=5,
        per_device_train_batch_size=2,
        save_steps=100,
        save_total_limit=2,
        learning_rate=1e-5,
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
    trainer.save_model("./image2vue_trained_model")
    
    # 测试生成
    def generate_vue_code(image_path: str, max_length=512):
        image = Image.open(image_path).convert('RGB')
        pixel_values = image_processor(image, return_tensors="pt")["pixel_values"]
        
        outputs = model.generate(
            pixel_values,
            max_length=max_length,
            num_return_sequences=1,
            no_repeat_ngram_size=2,
            temperature=0.7
        )
        
        return tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # 测试生成效果
    test_image = "/Users/hongyaotang/src/py/pyagent/data/image2vue/test/test_image.jpg"
    print("\n测试生成：")
    print(f"输入图片: {test_image}")
    print("生成的 Vue 代码:")
    print(generate_vue_code(test_image))

if __name__ == "__main__":
    main()