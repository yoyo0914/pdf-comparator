import os
import json
from datetime import datetime

class SessionManager:
    def __init__(self, history_dir="history"):
        self.history_dir = history_dir
        os.makedirs(self.history_dir, exist_ok=True)
    
    def save_conversation_session(self, conversation_data, session_name=None):
        if session_name is None:
            session_name = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        safe_session_name = self._sanitize_filename(session_name)
        filename = f"conversation_{safe_session_name}.json"
        filepath = os.path.join(self.history_dir, filename)
        
        save_data = {
            "session_name": session_name,
            "created_time": datetime.now().isoformat(),
            "conversation_data": conversation_data
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def load_conversation_session(self, session_name):
        if session_name.endswith('.json') and os.path.exists(session_name):
            filepath = session_name
        else:
            safe_session_name = self._sanitize_filename(session_name)
            filename = f"conversation_{safe_session_name}.json"
            filepath = os.path.join(self.history_dir, filename)
        
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            save_data = json.load(f)
        
        return save_data.get('conversation_data', {})
    
    def list_conversation_sessions(self):
        sessions = []
        
        for filename in os.listdir(self.history_dir):
            if filename.startswith('conversation_') and filename.endswith('.json'):
                filepath = os.path.join(self.history_dir, filename)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                sessions.append({
                    'session_name': data.get('session_name', filename[:-5]),
                    'created_time': datetime.fromisoformat(data.get('created_time', '2024-01-01T00:00:00')),
                    'modified_time': datetime.fromtimestamp(os.path.getmtime(filepath)),
                    'filepath': filepath
                })
        
        sessions.sort(key=lambda x: x['modified_time'], reverse=True)
        return sessions
    
    def _sanitize_filename(self, filename):
        unsafe_chars = '<>:"/\\|?*'
        safe_filename = filename
        for char in unsafe_chars:
            safe_filename = safe_filename.replace(char, '_')
        
        if len(safe_filename) > 100:
            safe_filename = safe_filename[:100]
        
        return safe_filename