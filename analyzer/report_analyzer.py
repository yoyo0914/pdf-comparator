"""
智能財報分析器 - 分段分析大型PDF文件
"""
import os
import re
import json
from datetime import datetime
from typing import Dict, List, Any

class FinancialReportAnalyzer:
    def __init__(self, pdf_parser, qa_engine):
        self.pdf_parser = pdf_parser
        self.qa_engine = qa_engine
        
        # 財報分析框架
        self.analysis_framework = {
            "營收分析": {
                "keywords": ["營業收入", "收入", "營收", "銷售", "revenue"],
                "pages": range(1, 30),  # 通常在前面
                "metrics": ["成長率", "年增率", "季增率"]
            },
            "獲利能力分析": {
                "keywords": ["淨利", "獲利", "利潤", "margin", "profit"],
                "pages": range(1, 30),
                "metrics": ["毛利率", "營業利益率", "淨利率", "ROE", "ROA"]
            },
            "財務結構分析": {
                "keywords": ["資產", "負債", "股東權益", "debt", "equity"],
                "pages": range(1, 50),
                "metrics": ["負債比率", "流動比率", "速動比率"]
            },
            "現金流分析": {
                "keywords": ["現金流", "cash flow", "營運現金流"],
                "pages": range(1, 40),
                "metrics": ["自由現金流", "現金轉換週期"]
            },
            "投資分析": {
                "keywords": ["投資", "轉投資", "子公司", "investment"],
                "pages": range(30, 80),  # 通常在中後段
                "metrics": ["投資報酬率", "投資金額", "持股比例"]
            },
            "風險因子分析": {
                "keywords": ["風險", "不確定", "挑戰", "風險因子"],
                "pages": range(50, 120),  # 通常在後段
                "metrics": ["風險等級", "影響程度"]
            }
        }
    
    def generate_comprehensive_report(self, report_a_path, report_b_path):
        """生成完整的財報比較分析報告"""
        print("開始生成財報分析報告...")
        
        # 分析兩份報告
        analysis_a = self.analyze_single_report(report_a_path, "報告A")
        analysis_b = self.analyze_single_report(report_b_path, "報告B")
        
        # 生成比較報告
        comparison_report = self.generate_comparison_report(analysis_a, analysis_b)
        
        # 儲存報告
        report_path = f"reports/financial_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        self.save_report(comparison_report, report_path)
        
        return comparison_report, report_path
    
    def analyze_single_report(self, pdf_path, report_name):
        """分析單一財報"""
        print(f"分析{report_name}...")
        
        analysis_results = {}
        
        for category, config in self.analysis_framework.items():
            print(f"  分析{category}...")
            
            # 提取相關頁面內容
            relevant_content = self.extract_relevant_pages(
                pdf_path, config["pages"], config["keywords"]
            )
            
            if relevant_content:
                # AI分析
                analysis = self.analyze_category(category, relevant_content, config)
                analysis_results[category] = analysis
            else:
                analysis_results[category] = {"status": "無相關數據"}
        
        return analysis_results
    
    def extract_relevant_pages(self, pdf_path, page_range, keywords):
        """提取相關頁面內容"""
        try:
            import fitz
            doc = fitz.open(pdf_path)
            relevant_content = []
            
            for page_num in page_range:
                if page_num > len(doc):
                    break
                
                page = doc.load_page(page_num - 1)
                text = page.get_text()
                
                # 檢查是否包含關鍵字
                if any(keyword in text for keyword in keywords):
                    # 清理和截斷文字
                    clean_text = self.clean_text(text)
                    if len(clean_text) > 2000:  # 限制長度
                        clean_text = clean_text[:2000] + "..."
                    
                    relevant_content.append({
                        "page": page_num,
                        "content": clean_text
                    })
            
            doc.close()
            return relevant_content
            
        except Exception as e:
            print(f"提取頁面內容失敗: {str(e)}")
            return []
    
    def clean_text(self, text):
        """清理文字"""
        # 移除多餘空白和換行
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n', text)
        return text.strip()
    
    def analyze_category(self, category, content_list, config):
        """使用AI分析特定類別"""
        # 合併相關內容
        combined_content = "\n\n".join([
            f"第{item['page']}頁:\n{item['content']}" 
            for item in content_list[:5]  # 最多5頁
        ])
        
        # 構建分析提示詞
        prompt = f"""請分析以下財報內容中的{category}：

相關內容：
{combined_content}

請提供以下分析：
1. 關鍵數據摘要
2. 重要趨勢
3. 主要指標
4. 風險或機會

請用繁體中文回答，格式簡潔清楚。如果資料不足，請明確說明。"""

        try:
            response = self.qa_engine.generate_answer(prompt, temperature=0.2)
            
            return {
                "status": "已分析",
                "analysis": response,
                "pages_analyzed": [item['page'] for item in content_list],
                "data_quality": "良好" if len(content_list) >= 2 else "有限"
            }
            
        except Exception as e:
            return {
                "status": "分析失敗",
                "error": str(e),
                "pages_found": len(content_list)
            }
    
    def generate_comparison_report(self, analysis_a, analysis_b):
        """生成比較分析報告"""
        report = {
            "標題": "財報比較分析報告",
            "生成時間": datetime.now().strftime("%Y年%m月%d日 %H:%M"),
            "摘要": {},
            "詳細分析": {},
            "綜合評估": {}
        }
        
        # 生成各類別比較
        for category in self.analysis_framework.keys():
            if category in analysis_a and category in analysis_b:
                comparison = self.compare_category(
                    category, 
                    analysis_a[category], 
                    analysis_b[category]
                )
                report["詳細分析"][category] = comparison
        
        # 生成執行摘要
        report["摘要"] = self.generate_executive_summary(report["詳細分析"])
        
        # 生成綜合評估
        report["綜合評估"] = self.generate_overall_assessment(analysis_a, analysis_b)
        
        return report
    
    def compare_category(self, category, analysis_a, analysis_b):
        """比較特定類別"""
        if analysis_a.get("status") != "已分析" or analysis_b.get("status") != "已分析":
            return {
                "比較結果": "資料不足，無法比較",
                "報告A狀態": analysis_a.get("status", "未知"),
                "報告B狀態": analysis_b.get("status", "未知")
            }
        
        # 使用AI進行比較分析
        prompt = f"""請比較以下兩份財報的{category}：

報告A的{category}分析：
{analysis_a.get('analysis', '無資料')}

報告B的{category}分析：
{analysis_b.get('analysis', '無資料')}

請提供：
1. 主要差異點
2. 優劣勢比較
3. 建議關注重點

請用繁體中文回答，簡潔明瞭。"""

        try:
            comparison_result = self.qa_engine.generate_answer(prompt, temperature=0.2)
            
            return {
                "比較結果": comparison_result,
                "資料品質": {
                    "報告A": analysis_a.get("data_quality", "未知"),
                    "報告B": analysis_b.get("data_quality", "未知")
                },
                "分析頁面": {
                    "報告A": analysis_a.get("pages_analyzed", []),
                    "報告B": analysis_b.get("pages_analyzed", [])
                }
            }
            
        except Exception as e:
            return {
                "比較結果": f"比較分析失敗: {str(e)}",
                "錯誤": True
            }
    
    def generate_executive_summary(self, detailed_analysis):
        """生成執行摘要"""
        # 提取關鍵比較結果
        summary_points = []
        
        for category, analysis in detailed_analysis.items():
            if "比較結果" in analysis and not analysis.get("錯誤"):
                summary_points.append(f"**{category}**: {analysis['比較結果'][:200]}...")
        
        return {
            "關鍵發現": summary_points[:5],  # 最多5個要點
            "整體評估": "基於可獲得的財報資料進行比較分析",
            "資料覆蓋率": f"{len([a for a in detailed_analysis.values() if not a.get('錯誤')])}/{len(detailed_analysis)}"
        }
    
    def generate_overall_assessment(self, analysis_a, analysis_b):
        """生成綜合評估"""
        # 統計分析覆蓋率
        categories_a = sum(1 for a in analysis_a.values() if a.get("status") == "已分析")
        categories_b = sum(1 for a in analysis_b.values() if a.get("status") == "已分析")
        total_categories = len(self.analysis_framework)
        
        return {
            "分析完整度": {
                "報告A": f"{categories_a}/{total_categories} ({categories_a/total_categories*100:.1f}%)",
                "報告B": f"{categories_b}/{total_categories} ({categories_b/total_categories*100:.1f}%)"
            },
            "建議": [
                "本分析基於PDF文件自動提取的內容",
                "如需更深入分析，建議查看原始財報數據",
                "重要決策應結合多方資訊來源"
            ],
            "分析方法": "AI驅動的分段式財報分析"
        }
    
    def save_report(self, report, output_path):
        """儲存報告為Markdown格式"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        md_content = self.format_report_as_markdown(report)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        # 同時儲存JSON版本
        json_path = output_path.replace('.md', '.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"報告已儲存至: {output_path}")
        print(f"JSON資料已儲存至: {json_path}")
    
    def format_report_as_markdown(self, report):
        """格式化報告為Markdown"""
        md = f"""# {report['標題']}

**生成時間**: {report['生成時間']}

## 執行摘要

### 關鍵發現
"""
        
        for finding in report['摘要'].get('關鍵發現', []):
            md += f"- {finding}\n"
        
        md += f"\n**資料覆蓋率**: {report['摘要'].get('資料覆蓋率', '未知')}\n\n"
        
        md += "## 詳細分析\n\n"
        
        for category, analysis in report['詳細分析'].items():
            md += f"### {category}\n\n"
            md += f"{analysis.get('比較結果', '無分析結果')}\n\n"
            
            if '資料品質' in analysis:
                md += f"**資料品質**: 報告A: {analysis['資料品質']['報告A']}, 報告B: {analysis['資料品質']['報告B']}\n\n"
        
        md += "## 綜合評估\n\n"
        
        assessment = report['綜合評估']
        md += f"**分析完整度**:\n"
        md += f"- 報告A: {assessment['分析完整度']['報告A']}\n"
        md += f"- 報告B: {assessment['分析完整度']['報告B']}\n\n"
        
        md += "**建議**:\n"
        for suggestion in assessment.get('建議', []):
            md += f"- {suggestion}\n"
        
        md += f"\n**分析方法**: {assessment.get('分析方法', '未知')}\n"
        
        return md