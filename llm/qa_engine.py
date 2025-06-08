import requests
import json
import logging
import time
from typing import Optional, Dict, Any

class QAEngine:
    def __init__(self, 
                 model_name="llama3:latest",
                 ollama_url="http://localhost:11434",
                 timeout=120,
                 max_retries=3):
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.timeout = timeout
        self.max_retries = max_retries
        
        self.generate_url = f"{ollama_url}/api/generate"
        self.chat_url = f"{ollama_url}/api/chat"
        
        logging.getLogger(__name__).setLevel(logging.WARNING)
        
        self._check_ollama_connection()
    
    def _check_ollama_connection(self):
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                
                if self.model_name in model_names:
                    return
                
                llama3_models = [name for name in model_names if 'llama3' in name.lower()]
                
                if llama3_models:
                    self.model_name = llama3_models[0]
                    print(f"使用模型: {self.model_name}")
                    return
                
                print("未找到llama3模型")
                print(f"可用模型: {', '.join(model_names)}")
                print("請執行: ollama pull llama3")
                    
            else:
                print("Ollama服務異常")
                
        except requests.exceptions.RequestException:
            print(f"無法連接Ollama ({self.ollama_url})")
            print("確認服務已啟動: ollama serve")
    
    def generate_answer(self, prompt: str, temperature: float = 0.3, max_tokens: int = 2048) -> Optional[str]:
        for attempt in range(self.max_retries):
            try:
                payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                        "top_p": 0.9,
                        "repeat_penalty": 1.1
                    }
                }
                
                response = requests.post(
                    self.generate_url,
                    json=payload,
                    timeout=self.timeout,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    answer = result.get('response', '').strip()
                    
                    if answer:
                        processed_answer = self._process_answer(answer)
                        return processed_answer
                    else:
                        if attempt == 0:
                            print("模型回傳空回答")
                        
                else:
                    if attempt == 0:
                        print(f"API請求失敗: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                if attempt == 0:
                    print("請求超時，重試中...")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    
            except requests.exceptions.RequestException as e:
                if attempt == 0:
                    print(f"請求失敗: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    
            except Exception as e:
                print(f"未預期錯誤: {str(e)}")
                break
        
        return self._get_fallback_answer()
    
    def _process_answer(self, answer: str) -> str:
        answer = answer.strip()
        
        invalid_indicators = [
            "我不知道", "不清楚", "無法確定", "沒有足夠信息",
            "需要更多資料", "unable to", "don't know", "cannot determine",
            "insufficient information", "not enough data"
        ]
        
        answer_lower = answer.lower()
        has_invalid_indicator = any(indicator.lower() in answer_lower for indicator in invalid_indicators)
        
        is_too_short = len(answer) < 20
        
        has_quality = self._check_answer_quality(answer)
        
        if has_invalid_indicator or is_too_short or not has_quality:
            return "抱歉，根據提供的資料我無法回答這個問題。請嘗試重新表述您的問題，或確認問題是否與財報內容相關。"
        
        return answer
    
    def _check_answer_quality(self, answer: str) -> bool:
        if len(answer.strip()) < 10:
            return False
        
        question_words = ["什麼", "如何", "為什麼", "哪裡", "何時", "誰"]
        if any(word in answer for word in question_words) and len(answer) < 50:
            return False
        
        has_numbers = any(char.isdigit() for char in answer)
        has_currency = any(symbol in answer for symbol in ["元", "萬", "億", "$", "NT", "USD"])
        has_percentage = "%" in answer
        
        return has_numbers or has_currency or has_percentage or len(answer) > 100
    
    def _get_fallback_answer(self) -> str:
        return "目前無法連接到語言模型服務。請檢查Ollama服務是否正常運行。"
    
    def chat_with_context(self, messages: list, temperature: float = 0.3) -> Optional[str]:
        try:
            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            }
            
            response = requests.post(
                self.chat_url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('message', {}).get('content', '').strip()
                return self._process_answer(answer) if answer else None
            else:
                return None
                
        except Exception:
            return None
    
    def get_model_info(self) -> Dict[str, Any]:
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                current_model = next((m for m in models if m['name'] == self.model_name), None)
                
                return {
                    "model_name": self.model_name,
                    "ollama_url": self.ollama_url,
                    "model_available": current_model is not None,
                    "model_details": current_model,
                    "all_models": [m['name'] for m in models]
                }
            else:
                return {"error": f"無法獲取模型資訊: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"連接錯誤: {str(e)}"}