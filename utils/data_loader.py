"""
資料載入器
"""
import os
import json
import logging
from datetime import datetime

class DataLoader:
    def __init__(self, outputs_dir="outputs", history_dir="history"):
        self.outputs_dir = outputs_dir
        self.history_dir = history_dir
        
        os.makedirs(self.outputs_dir, exist_ok=True)
        os.makedirs(self.history_dir, exist_ok=True)
        
        logging.getLogger(__name__).setLevel(logging.CRITICAL)
    
    def load_report_texts(self):
        reports = {}
        
        report_a_path = os.path.join(self.outputs_dir, "report_a_text.txt")
        reports['report_a'] = self._load_text_file(report_a_path)
        
        report_b_path = os.path.join(self.outputs_dir, "report_b_text.txt")
        reports['report_b'] = self._load_text_file(report_b_path)
        
        return reports
    
    def _load_text_file(self, filepath):
        try:
            if not os.path.exists(filepath):
                return ""
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return content
            
        except Exception:
            return ""
    
    def check_reports_availability(self):
        report_a_path = os.path.join(self.outputs_dir, "report_a_text.txt")
        report_b_path = os.path.join(self.outputs_dir, "report_b_text.txt")
        
        status = {
            'report_a_exists': os.path.exists(report_a_path),
            'report_b_exists': os.path.exists(report_b_path),
            'both_available': False,
            'report_a_size': 0,
            'report_b_size': 0
        }
        
        if status['report_a_exists']:
            status['report_a_size'] = os.path.getsize(report_a_path)
        
        if status['report_b_exists']:
            status['report_b_size'] = os.path.getsize(report_b_path)
        
        status['both_available'] = (
            status['report_a_exists'] and 
            status['report_b_exists'] and
            status['report_a_size'] > 0 and 
            status['report_b_size'] > 0
        )
        
        return status
    
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
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            return filepath
            
        except Exception:
            return None
    
    def load_conversation_session(self, session_name):
        if session_name.endswith('.json') and os.path.exists(session_name):
            filepath = session_name
        else:
            safe_session_name = self._sanitize_filename(session_name)
            filename = f"conversation_{safe_session_name}.json"
            filepath = os.path.join(self.history_dir, filename)
        
        try:
            if not os.path.exists(filepath):
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            return save_data.get('conversation_data', {})
            
        except Exception:
            return None
    
    def list_conversation_sessions(self):
        sessions = []
        
        try:
            for filename in os.listdir(self.history_dir):
                if filename.startswith('conversation_') and filename.endswith('.json'):
                    filepath = os.path.join(self.history_dir, filename)
                    
                    stat = os.stat(filepath)
                    created_time = datetime.fromtimestamp(stat.st_ctime)
                    modified_time = datetime.fromtimestamp(stat.st_mtime)
                    file_size = stat.st_size
                    
                    session_name = filename.replace('conversation_', '').replace('.json', '')
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            session_name = data.get('session_name', session_name)
                    except:
                        pass
                    
                    sessions.append({
                        'filename': filename,
                        'filepath': filepath,
                        'session_name': session_name,
                        'created_time': created_time,
                        'modified_time': modified_time,
                        'file_size': file_size
                    })
            
            sessions.sort(key=lambda x: x['modified_time'], reverse=True)
            
        except Exception:
            pass
        
        return sessions
    
    def delete_conversation_session(self, session_name):
        safe_session_name = self._sanitize_filename(session_name)
        filename = f"conversation_{safe_session_name}.json"
        filepath = os.path.join(self.history_dir, filename)
        
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            else:
                return False
                
        except Exception:
            return False
    
    def _sanitize_filename(self, filename):
        unsafe_chars = '<>:"/\\|?*'
        safe_filename = filename
        for char in unsafe_chars:
            safe_filename = safe_filename.replace(char, '_')
        
        if len(safe_filename) > 100:
            safe_filename = safe_filename[:100]
        
        return safe_filename
    
    def get_storage_info(self):
        info = {
            'outputs_dir': self.outputs_dir,
            'history_dir': self.history_dir,
            'outputs_exists': os.path.exists(self.outputs_dir),
            'history_exists': os.path.exists(self.history_dir),
            'total_sessions': 0,
            'total_history_size': 0
        }
        
        try:
            if os.path.exists(self.history_dir):
                for filename in os.listdir(self.history_dir):
                    if filename.endswith('.json'):
                        filepath = os.path.join(self.history_dir, filename)
                        info['total_sessions'] += 1
                        info['total_history_size'] += os.path.getsize(filepath)
        
        except Exception:
            pass
        
        return info