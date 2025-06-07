import os
import sys
import argparse
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from parser.pdf_parser import PDFParser
from utils.session_manager import SessionManager
from semantic import SemanticRetriever
from llm.qa_engine import QAEngine
from analyzer.report_analyzer import FinancialReportAnalyzer

class FinancialAnalysisSystem:
    def __init__(self):
        self.pdf_parser = PDFParser()
        self.session_manager = SessionManager()
        self.semantic_retriever = SemanticRetriever()
        self.qa_engine = QAEngine()
        self.report_analyzer = FinancialReportAnalyzer(self.pdf_parser, self.qa_engine)
        
        self.reports_loaded = False
        self.current_session = None
        self.conversation_history = []
        
        print("財報比較分析系統")
    
    def run_analysis_mode(self, report_a_path=None, report_b_path=None):
        if not report_a_path:
            report_a_path = "data/report_a.pdf"
        if not report_b_path:
            report_b_path = "data/report_b.pdf"
        
        print("\n智能財報分析模式")
        
        report, report_path = self.report_analyzer.generate_comprehensive_report(
            report_a_path, report_b_path
        )
        
        print(f"\n分析完成")
        print(f"報告路徑: {report_path}")
        
        self.display_report_summary(report)
        return True
    
    def run_chat_mode(self, report_a_path=None, report_b_path=None, force_reparse=False):
        print("\n對話問答模式")
        
        self.setup_reports(report_a_path, report_b_path, force_reparse)
        
        if self.reports_loaded:
            self.start_conversation()
        else:
            print("無法載入財報進行問答")
            return False
    
    def setup_reports(self, report_a_path=None, report_b_path=None, force_reparse=False):
        if not report_a_path:
            report_a_path = "data/report_a.pdf"
        if not report_b_path:
            report_b_path = "data/report_b.pdf"
        
        report_a_output = "outputs/report_a_agent.txt"
        report_b_output = "outputs/report_b_agent.txt"
        
        if force_reparse or not os.path.exists(report_a_output) or not os.path.exists(report_b_output):
            print("解析PDF中...")
            self.pdf_parser.extract_text_from_pdf(report_a_path, report_a_output)
            self.pdf_parser.extract_text_from_pdf(report_b_path, report_b_output)
        
        with open(report_a_output, 'r', encoding='utf-8') as f:
            report_a_text = f.read()
        with open(report_b_output, 'r', encoding='utf-8') as f:
            report_b_text = f.read()
        
        print("建立TF-IDF索引...")
        self.semantic_retriever.chunk_documents(report_a_text, report_b_text)
        self.semantic_retriever.build_index()
        
        self.reports_loaded = True
        print("PDF解析完成")
    
    def start_conversation(self):
        print("\n對話模式已啟動")
        print("輸入 'quit' 退出")
        
        while True:
            question = input("\n您的問題: ").strip()
            
            if question.lower() in ['quit', 'exit']:
                break
            elif question.lower() == 'save':
                self._save_conversation()
            elif question.lower() == 'load':
                self._load_conversation()
            elif question.lower() == 'clear':
                self._clear_conversation()
            elif question:
                print("思考中...")
                answer = self._get_answer(question)
                if answer:
                    print(f"\n{answer}")
                    self.conversation_history.append({
                        "user": question,
                        "assistant": answer
                    })
                else:
                    print("無法生成回答")
    
    def _get_answer(self, question):
        relevant_context, selected_chunks = self.semantic_retriever.smart_context_selection(question)
        
        if not relevant_context:
            return "未找到相關內容，請重新表述問題"
        
        system_prompt = """你是專業的財務分析助手。請基於提供的相關財報內容回答問題。

回答要求：
1. 使用繁體中文
2. 基於提供的內容準確回答
3. 引用具體數字支持回答
4. 如果內容不足以回答問題，請明確說明
5. 比較兩份報告時請明確標示報告來源"""

        conversation_context = ""
        if self.conversation_history:
            recent_history = self.conversation_history[-3:]
            for i, conv in enumerate(recent_history, 1):
                conversation_context += f"\n對話{i}:\n問: {conv['user']}\n答: {conv['assistant'][:100]}...\n"

        prompt = f"""{system_prompt}

相關財報內容:
{relevant_context}

對話歷史:
{conversation_context}

問題: {question}

請基於以上內容用繁體中文詳細回答。"""

        return self.qa_engine.generate_answer(prompt)
    
    def _save_conversation(self):
        if not self.conversation_history:
            print("無對話記錄可儲存")
            return
        
        session_name = input("會話名稱 (按Enter使用時間): ").strip()
        if not session_name:
            session_name = datetime.now().strftime("%m%d_%H%M")
        
        data = {
            "conversation_history": self.conversation_history,
            "summary": {"total_conversations": len(self.conversation_history)}
        }
        
        filepath = self.session_manager.save_conversation_session(data, session_name)
        if filepath:
            print(f"已儲存: {session_name}")
            self.current_session = session_name
        else:
            print("儲存失敗")
    
    def _load_conversation(self):
        sessions = self.session_manager.list_conversation_sessions()
        
        if not sessions:
            print("無歷史對話")
            return
        
        print("\n對話會話:")
        for i, session in enumerate(sessions[:5], 1):
            time_str = session['modified_time'].strftime("%m/%d %H:%M")
            print(f"  {i}. {session['session_name']} ({time_str})")
        
        choice = input("\n選擇編號 (按Enter取消): ").strip()
        if not choice:
            return
        
        index = int(choice) - 1
        if 0 <= index < len(sessions):
            session = sessions[index]
            data = self.session_manager.load_conversation_session(session['session_name'])
            
            if data:
                self.conversation_history = data.get('conversation_history', [])
                self.current_session = session['session_name']
                print(f"載入: {session['session_name']}")
            else:
                print("載入失敗")
        else:
            print("無效選擇")
    
    def _clear_conversation(self):
        if input("確定清除對話？(y/N): ").strip().lower() in ['y', 'yes']:
            self.conversation_history = []
            self.current_session = None
            print("已清除")
        else:
            print("已取消")
    
    def display_report_summary(self, report):
        print("\n分析結果摘要")
        
        summary = report.get('摘要', {})
        findings = summary.get('關鍵發現', [])
        
        if findings:
            print("\n關鍵發現:")
            for i, finding in enumerate(findings[:3], 1):
                clean_finding = finding.replace('**', '').replace('*', '')
                if len(clean_finding) > 100:
                    clean_finding = clean_finding[:100] + "..."
                print(f"{i}. {clean_finding}")
        
        assessment = report.get('綜合評估', {})
        completeness = assessment.get('分析完整度', {})
        
        if completeness:
            print(f"\n分析完整度:")
            print(f"  報告A: {completeness.get('報告A', '未知')}")
            print(f"  報告B: {completeness.get('報告B', '未知')}")


def main():
    parser = argparse.ArgumentParser(description="財報比較分析系統")
    parser.add_argument("--report-a", help="財報A路徑")
    parser.add_argument("--report-b", help="財報B路徑")
    parser.add_argument("--mode", choices=['analysis', 'chat'], default='analysis')
    parser.add_argument("--force-reparse", action="store_true", help="強制重新解析")
    
    args = parser.parse_args()
    
    system = FinancialAnalysisSystem()
    
    if args.mode == 'analysis':
        success = system.run_analysis_mode(args.report_a, args.report_b)
        
        if success:
            choice = input("\n是否進入問答模式進行額外查詢？(y/N): ").strip().lower()
            if choice in ['y', 'yes']:
                system.run_chat_mode(args.report_a, args.report_b, args.force_reparse)
    
    elif args.mode == 'chat':
        system.run_chat_mode(args.report_a, args.report_b, args.force_reparse)


if __name__ == "__main__":
    main()