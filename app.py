"""
財報比較分析系統 - 智能分析版
"""
import os
import sys
import argparse
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from parser.pdf_parser import PDFParser
from utils.data_loader import DataLoader
from utils.prompt_builder import PromptBuilder
from llm.qa_engine import QAEngine
from analyzer.report_analyzer import FinancialReportAnalyzer

class FinancialAnalysisSystem:
    def __init__(self):
        self.pdf_parser = PDFParser()
        self.data_loader = DataLoader()
        self.prompt_builder = PromptBuilder()
        self.qa_engine = QAEngine()
        self.report_analyzer = FinancialReportAnalyzer(self.pdf_parser, self.qa_engine)
        
        self.reports_loaded = False
        self.current_session = None
        
        print("財報比較分析系統")
        print("=" * 40)
    
    def run_analysis_mode(self, report_a_path=None, report_b_path=None):
        """運行分析模式 - 生成完整分析報告"""
        if not report_a_path:
            report_a_path = "data/report_a.pdf"
        if not report_b_path:
            report_b_path = "data/report_b.pdf"
        
        # 檢查檔案
        if not os.path.exists(report_a_path):
            print(f"找不到財報A: {report_a_path}")
            return False
        
        if not os.path.exists(report_b_path):
            print(f"找不到財報B: {report_b_path}")
            return False
        
        print("\n=== 智能財報分析模式 ===")
        print("此模式將生成完整的財報比較分析報告")
        print("分析範圍: 營收、獲利、財務結構、現金流、投資、風險")
        print()
        
        try:
            # 生成分析報告
            report, report_path = self.report_analyzer.generate_comprehensive_report(
                report_a_path, report_b_path
            )
            
            print(f"\n分析完成！")
            print(f"報告路徑: {report_path}")
            print()
            
            # 顯示摘要
            self.display_report_summary(report)
            
            return True
            
        except Exception as e:
            print(f"分析失敗: {str(e)}")
            return False
    
    def display_report_summary(self, report):
        """顯示報告摘要"""
        print("=== 分析結果摘要 ===")
        print()
        
        # 顯示關鍵發現
        summary = report.get('摘要', {})
        findings = summary.get('關鍵發現', [])
        
        if findings:
            print("關鍵發現:")
            for i, finding in enumerate(findings[:3], 1):
                # 清理格式
                clean_finding = finding.replace('**', '').replace('*', '')
                if len(clean_finding) > 100:
                    clean_finding = clean_finding[:100] + "..."
                print(f"{i}. {clean_finding}")
            print()
        
        # 顯示分析完整度
        assessment = report.get('綜合評估', {})
        completeness = assessment.get('分析完整度', {})
        
        if completeness:
            print("分析完整度:")
            print(f"  報告A: {completeness.get('報告A', '未知')}")
            print(f"  報告B: {completeness.get('報告B', '未知')}")
            print()
        
        # 顯示詳細分析類別
        detailed = report.get('詳細分析', {})
        successful_categories = [cat for cat, data in detailed.items() 
                               if not data.get('錯誤', False)]
        
        if successful_categories:
            print(f"成功分析類別 ({len(successful_categories)}個):")
            for category in successful_categories:
                print(f"  - {category}")
            print()
        
        print("請查看完整報告檔案以獲得詳細分析結果。")
        print()
    
    def run_chat_mode(self, report_a_path=None, report_b_path=None, force_reparse=False):
        """運行對話模式 - 原有的問答功能"""
        print("\n=== 對話問答模式 ===")
        print("此模式支援自由問答，但受模型上下文長度限制")
        print()
        
        self.setup_reports(report_a_path, report_b_path, force_reparse)
        
        if self.reports_loaded:
            self.start_conversation()
        else:
            print("無法載入財報進行問答")
            return False
    
    def setup_reports(self, report_a_path=None, report_b_path=None, force_reparse=False):
        """設定財報檔案 (用於問答模式)"""
        if not report_a_path:
            report_a_path = "data/report_a.pdf"
        if not report_b_path:
            report_b_path = "data/report_b.pdf"
        
        status = self.data_loader.check_reports_availability()
        
        if status['both_available'] and not force_reparse:
            print("載入已解析的財報")
            self._load_existing_reports()
        else:
            self._parse_pdf_reports(report_a_path, report_b_path)
    
    def _load_existing_reports(self):
        """載入已存在的財報文字檔"""
        try:
            reports = self.data_loader.load_report_texts()
            
            if reports['report_a'] and reports['report_b']:
                # 截斷內容以避免上下文過長
                max_length = 10000  # 減少長度
                truncated_a = self._truncate_text(reports['report_a'], max_length)
                truncated_b = self._truncate_text(reports['report_b'], max_length)
                
                self.prompt_builder.set_report_contents(truncated_a, truncated_b)
                self.reports_loaded = True
                print("財報載入完成 (已截斷至適當長度)")
            else:
                print("文字檔為空，需重新解析")
                self.reports_loaded = False
                
        except Exception as e:
            print(f"載入失敗: {str(e)}")
            self.reports_loaded = False
    
    def _truncate_text(self, text, max_length):
        """截斷文字到指定長度"""
        if len(text) <= max_length:
            return text
        
        # 嘗試在句號處截斷
        truncated = text[:max_length]
        last_period = truncated.rfind('。')
        
        if last_period > max_length * 0.8:
            return truncated[:last_period + 1] + "\n\n[為避免上下文過長，內容已截斷。如需完整分析，請使用分析模式。]"
        else:
            return truncated + "\n\n[為避免上下文過長，內容已截斷。如需完整分析，請使用分析模式。]"
    
    def _parse_pdf_reports(self, report_a_path, report_b_path):
        """解析PDF財報"""
        if not os.path.exists(report_a_path):
            print(f"找不到財報A: {report_a_path}")
            return False
        
        if not os.path.exists(report_b_path):
            print(f"找不到財報B: {report_b_path}")
            return False
        
        try:
            print("解析PDF中...")
            results = self.pdf_parser.process_reports(report_a_path, report_b_path)
            
            if results['report_a'] and results['report_b']:
                # 截斷內容
                max_length = 10000
                truncated_a = self._truncate_text(results['report_a'], max_length)
                truncated_b = self._truncate_text(results['report_b'], max_length)
                
                self.prompt_builder.set_report_contents(truncated_a, truncated_b)
                self.reports_loaded = True
                print("PDF解析完成 (已截斷至適當長度)")
                return True
            else:
                print("解析失敗")
                return False
                
        except Exception as e:
            print(f"解析錯誤: {str(e)}")
            return False
    
    def start_conversation(self):
        """開始對話模式"""
        print("\n對話模式已啟動")
        print("注意: 受上下文長度限制，僅載入部分內容")
        print("輸入 'help' 查看指令，'quit' 退出")
        print("-" * 40)
        
        while True:
            try:
                user_input = input("\n您的問題: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', '退出']:
                    print("再見")
                    break
                elif user_input.lower() == 'help':
                    self._show_help()
                    continue
                elif user_input.lower() == 'save':
                    self._save_conversation()
                    continue
                elif user_input.lower() == 'load':
                    self._load_conversation()
                    continue
                elif user_input.lower() == 'clear':
                    self._clear_conversation()
                    continue
                elif user_input.lower() == 'status':
                    self._show_status()
                    continue
                
                print("思考中...")
                answer = self._get_answer(user_input)
                
                if answer:
                    print(f"\n{answer}\n")
                    self.prompt_builder.add_conversation(user_input, answer)
                else:
                    print("無法獲得回答")
                
            except KeyboardInterrupt:
                print("\n程式中斷")
                break
            except Exception as e:
                print(f"錯誤: {str(e)}")
    
    def _get_answer(self, question):
        """獲取問題回答"""
        try:
            full_prompt = self.prompt_builder.build_full_prompt(question)
            
            # 檢查prompt長度
            if len(full_prompt) > 15000:
                return "問題內容過長，建議使用分析模式獲得更完整的答案。"
            
            answer = self.qa_engine.generate_answer(full_prompt)
            return answer
        except Exception as e:
            print(f"回答生成錯誤: {str(e)}")
            return None
    
    def _show_help(self):
        """顯示幫助"""
        help_text = """
指令說明:
  quit/exit  - 退出程式
  save       - 儲存對話
  load       - 載入對話
  clear      - 清除歷史
  status     - 系統狀態
  help       - 顯示此說明

問題範例 (受上下文長度限制):
  • 報告A的主要營收來源
  • 兩家公司的獲利能力比較
  • 財務結構有何差異

注意: 如需完整分析，建議使用分析模式
        """
        print(help_text)
    
    def _save_conversation(self):
        """儲存對話"""
        if not self.prompt_builder.conversation_history:
            print("無對話記錄可儲存")
            return
        
        session_name = input("會話名稱 (按Enter使用時間): ").strip()
        if not session_name:
            session_name = datetime.now().strftime("%m%d_%H%M")
        
        data = {
            "conversation_history": self.prompt_builder.conversation_history,
            "summary": self.prompt_builder.get_conversation_summary()
        }
        
        if self.data_loader.save_conversation_session(data, session_name):
            print(f"已儲存: {session_name}")
            self.current_session = session_name
        else:
            print("儲存失敗")
    
    def _load_conversation(self):
        """載入對話"""
        sessions = self.data_loader.list_conversation_sessions()
        
        if not sessions:
            print("無歷史對話")
            return
        
        print("\n對話會話:")
        for i, session in enumerate(sessions[:5], 1):
            time_str = session['modified_time'].strftime("%m/%d %H:%M")
            print(f"  {i}. {session['session_name']} ({time_str})")
        
        try:
            choice = input("\n選擇編號 (按Enter取消): ").strip()
            if not choice:
                return
            
            index = int(choice) - 1
            if 0 <= index < len(sessions):
                session = sessions[index]
                data = self.data_loader.load_conversation_session(session['session_name'])
                
                if data:
                    self.prompt_builder.conversation_history = data.get('conversation_history', [])
                    self.current_session = session['session_name']
                    print(f"載入: {session['session_name']}")
                else:
                    print("載入失敗")
            else:
                print("無效選擇")
                
        except ValueError:
            print("請輸入數字")
        except Exception as e:
            print(f"載入錯誤: {str(e)}")
    
    def _clear_conversation(self):
        """清除對話歷史"""
        if input("確定清除對話？(y/N): ").strip().lower() in ['y', 'yes']:
            self.prompt_builder.clear_conversation_history()
            self.current_session = None
            print("已清除")
        else:
            print("已取消")
    
    def _show_status(self):
        """顯示系統狀態"""
        print(f"\n系統狀態:")
        print(f"  財報: {'已載入(截斷版)' if self.reports_loaded else '未載入'}")
        print(f"  對話: {len(self.prompt_builder.conversation_history)} 輪")
        print(f"  會話: {self.current_session or '未儲存'}")
        
        model_info = self.qa_engine.get_model_info()
        model_ok = model_info.get('model_available', False)
        print(f"  模型: {'已連接' if model_ok else '未連接'} {self.qa_engine.model_name}")


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="財報比較分析系統")
    parser.add_argument("--report-a", help="財報A路徑")
    parser.add_argument("--report-b", help="財報B路徑")
    parser.add_argument("--mode", choices=['analysis', 'chat'], default='analysis',
                       help="運行模式: analysis(分析模式) 或 chat(問答模式)")
    parser.add_argument("--force-reparse", action="store_true", help="強制重新解析")
    
    args = parser.parse_args()
    
    try:
        system = FinancialAnalysisSystem()
        
        if args.mode == 'analysis':
            # 分析模式 - 生成完整報告
            success = system.run_analysis_mode(args.report_a, args.report_b)
            
            if success:
                # 詢問是否進入問答模式
                choice = input("\n是否進入問答模式進行額外查詢？(y/N): ").strip().lower()
                if choice in ['y', 'yes']:
                    system.run_chat_mode(args.report_a, args.report_b, args.force_reparse)
        
        elif args.mode == 'chat':
            # 問答模式
            system.run_chat_mode(args.report_a, args.report_b, args.force_reparse)
    
    except KeyboardInterrupt:
        print("\n程式結束")
    except Exception as e:
        print(f"錯誤: {str(e)}")


if __name__ == "__main__":
    main()