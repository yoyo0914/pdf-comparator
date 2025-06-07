import json
from datetime import datetime

class PromptBuilder:
    def __init__(self, max_history_length=10):
        self.max_history_length = max_history_length
        self.conversation_history = []
        self.report_a_content = ""
        self.report_b_content = ""
        
    def set_report_contents(self, report_a_text, report_b_text):
        self.report_a_content = report_a_text
        self.report_b_content = report_b_text
    
    def add_conversation(self, user_question, assistant_answer):
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "user": user_question,
            "assistant": assistant_answer
        }
        
        self.conversation_history.append(conversation)
        
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length:]
    
    def build_system_prompt(self):
        return """你是一個專業的財務分析助手，專門協助用戶分析比較兩份財務報告。

重要指示：
1. 必須使用繁體中文回答
2. 基於提供的兩份財報內容（報告A和報告B）來回答問題
3. 當進行比較時，請明確指出是哪份報告的數據
4. 如果問題涉及的資訊在報告中找不到，請回答「抱歉，根據提供的資料我無法回答這個問題。」
5. 回答要準確、客觀，避免推測
6. 可以引用具體的數字和段落來支持你的回答
7. 回答格式要簡潔清楚，重點突出

請確保所有回答都使用繁體中文，並基於提供的財報內容。"""
        
    def build_context_prompt(self):
        context_prompt = f"""
=== 財務報告內容 ===

【報告A內容】
{self._truncate_content(self.report_a_content, 15000)}

【報告B內容】  
{self._truncate_content(self.report_b_content, 15000)}

=== 對話歷史 ===
"""
        
        if self.conversation_history:
            for i, conv in enumerate(self.conversation_history, 1):
                context_prompt += f"\n第{i}輪對話：\n"
                context_prompt += f"用戶問題: {conv['user']}\n"
                context_prompt += f"助手回答: {conv['assistant']}\n"
        else:
            context_prompt += "\n(這是第一輪對話)\n"
        
        return context_prompt
    
    def build_full_prompt(self, user_question):
        system_prompt = self.build_system_prompt()
        context_prompt = self.build_context_prompt()
        
        full_prompt = f"""{system_prompt}

{context_prompt}

=== 當前問題 ===
用戶問題: {user_question}

請使用繁體中文，基於上述報告內容和對話歷史來回答用戶的問題。如果無法根據提供的資料回答，請明確說明。
重要：回答必須是繁體中文。"""
        
        return full_prompt
    
    def _truncate_content(self, content, max_length):
        if len(content) <= max_length:
            return content
        
        truncated = content[:max_length]
        last_period = truncated.rfind('。')
        if last_period > max_length * 0.8:
            return truncated[:last_period + 1] + "\n\n[內容過長，已截斷...]"
        else:
            return truncated + "\n\n[內容過長，已截斷...]"
    
    def get_conversation_summary(self):
        return {
            "total_conversations": len(self.conversation_history),
            "has_report_content": bool(self.report_a_content and self.report_b_content),
            "report_a_length": len(self.report_a_content),
            "report_b_length": len(self.report_b_content)
        }
    
    def save_conversation_history(self, filepath):
        data = {
            "conversation_history": self.conversation_history,
            "summary": self.get_conversation_summary()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_conversation_history(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.conversation_history = data.get('conversation_history', [])
                return True
        except FileNotFoundError:
            return False
        except Exception:
            return False
    
    def clear_conversation_history(self):
        self.conversation_history = []