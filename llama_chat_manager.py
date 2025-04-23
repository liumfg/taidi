from llama_cpp import Llama
import time

class LlamaChatManager:
    def __init__(self):
        """初始化Llama聊天管理器"""
        # 使用正确的路径格式
        self.model_path = "models/Llama3-q4_k_m-v1.gguf"
        
        # 加载GGUF模型
        self.model = Llama(
            model_path=self.model_path,
            n_ctx=4096,  # 上下文窗口大小
            n_gpu_layers=-1  # 使用所有可用的GPU层
        )
        
        # 对话历史
        self.history = []
        
    def format_prompt(self, user_input):
        """格式化输入提示"""
        system_prompt = "你是一个可爱活泼的桌面宠物，要用温暖幽默的语气回复主人，在对话中要加入可爱的动作描写。"
        
        # 构建完整的提示
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # 添加历史对话
        messages.extend(self.history)
        
        # 添加当前输入
        messages.append({"role": "user", "content": user_input})
        
        return messages
    
    def get_response(self, user_input):
        """获取模型回应"""
        try:
            # 准备输入
            messages = self.format_prompt(user_input)
            
            # 生成回应
            start_time = time.time()
            response = self.model.create_chat_completion(
                messages=messages,
                temperature=0.7,
                top_p=0.9,
                max_tokens=512
            )
            end_time = time.time()
            
            print(f"生成回应耗时: {end_time - start_time:.2f}秒")
            
            # 提取助手的回复部分
            assistant_response = response["choices"][0]["message"]["content"]
            
            # 更新对话历史
            self.history.append({"role": "user", "content": user_input})
            self.history.append({"role": "assistant", "content": assistant_response})
            
            # 保持历史长度在合理范围
            if len(self.history) > 20:  # 保留最近10轮对话
                self.history = self.history[-20:]
            
            return assistant_response
            
        except Exception as e:
            print(f"生成回应时出错: {e}")
            return "*揉揉眼睛* 抱歉主人，我有点累了，我们待会再聊吧～" 