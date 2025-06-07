import os
import json
from datetime import datetime

class FinancialReportAnalyzer:
    def __init__(self, pdf_parser, qa_engine):
        self.pdf_parser = pdf_parser
        self.qa_engine = qa_engine
        
        self.analysis_framework = {
            "營收分析": ["營收", "收入", "營業收入", "銷售", "revenue", "sales"],
            "獲利能力分析": ["獲利", "盈利", "淨利", "毛利", "profit", "earnings", "margin"],
            "財務結構分析": ["資產", "負債", "權益", "資本", "debt", "equity", "assets"],
            "現金流分析": ["現金流", "現金", "資金", "cash flow", "operating cash"],
            "投資分析": ["投資", "資本支出", "研發", "capex", "investment", "R&D"],
            "風險因子分析": ["風險", "不確定", "挑戰", "risk", "uncertainty", "challenge"]
        }
    
    def generate_comprehensive_report(self, report_a_path, report_b_path):
        print("開始生成分析報告...")
        
        print("解析PDF檔案...")
        text_a = self._parse_pdf_report(report_a_path, "report_a")
        text_b = self._parse_pdf_report(report_b_path, "report_b")
        
        print(f"PDF解析完成 - 報告A: {len(text_a)} 字符")
        print(f"PDF解析完成 - 報告B: {len(text_b)} 字符")
        
        analysis_a = {}
        analysis_b = {}
        
        print("分析報告A...")
        for category, keywords in self.analysis_framework.items():
            print(f"  分析{category}...")
            content_sections = self.extract_relevant_content(text_a, keywords, category)
            analysis_a[category] = self.analyze_category_from_content(category, content_sections, {})
        
        print("分析報告B...")
        for category, keywords in self.analysis_framework.items():
            print(f"  分析{category}...")
            content_sections = self.extract_relevant_content(text_b, keywords, category)
            analysis_b[category] = self.analyze_category_from_content(category, content_sections, {})
        
        report = self.generate_comparison_report(analysis_a, analysis_b)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"reports/financial_analysis_{timestamp}.md"
        json_path = f"reports/financial_analysis_{timestamp}.json"
        
        os.makedirs("reports", exist_ok=True)
        
        markdown_content = self.format_report_as_markdown(report)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"報告已儲存至: {output_path}")
        print(f"JSON資料已儲存至: {json_path}")
        
        return report, output_path
    
    def _parse_pdf_report(self, pdf_path, report_name):
        output_path = f"outputs/{report_name}_agent.txt"
        
        if not os.path.exists(output_path):
            self.pdf_parser.extract_text_from_pdf(pdf_path, output_path)
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return content
    
    def extract_relevant_content(self, full_content, keywords, category):
        if not full_content:
            return []
        
        relevant_sections = []
        lines = full_content.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            if any(keyword.lower() in line_lower for keyword in keywords):
                start_idx = max(0, i - 10)
                end_idx = min(len(lines), i + 10)
                
                context_lines = lines[start_idx:end_idx]
                context = '\n'.join(context_lines).strip()
                
                if len(context) > 50: 
                    relevant_sections.append({
                        "line_number": i,
                        "keyword_found": [kw for kw in keywords if kw.lower() in line_lower],
                        "content": context[:3000]  
                    })
        
        unique_sections = []
        used_content = set()
        
        for section in relevant_sections[:5]:  
            content_hash = hash(section["content"][:100])
            if content_hash not in used_content:
                unique_sections.append(section)
                used_content.add(content_hash)
        
        print(f"    找到 {len(unique_sections)} 個相關片段")
        return unique_sections
    
    def analyze_category_from_content(self, category, content_sections, config):
        if not content_sections:
            return {"status": "無內容可分析"}
        
        combined_content = "\n\n".join([
            f"片段 {i+1} (關鍵字: {section['keyword_found']}):\n{section['content']}" 
            for i, section in enumerate(content_sections)
        ])
        
        prompt = f"""請分析內容中的{category}：

相關內容：
{combined_content}

請提供以下分析（請用繁體中文）：
1. 關鍵數據摘要（具體數字和金額）
2. 重要趨勢和變化
3. 主要指標和比率
4. 風險或機會評估

格式簡潔清楚。"""

        response = self.qa_engine.generate_answer(prompt, temperature=0.1)
        
        return {
            "status": "已分析",
            "analysis": response,
            "sections_analyzed": len(content_sections),
            "keywords_found": [kw for section in content_sections for kw in section['keyword_found']],
            "data_quality": "良好" if len(content_sections) >= 2 else "有限"
        }
    
    def generate_comparison_report(self, analysis_a, analysis_b):
        report = {
            "標題": "財報比較分析報告",
            "生成時間": datetime.now().strftime("%Y年%m月%d日 %H:%M"),
            "摘要": {},
            "詳細分析": {},
            "綜合評估": {}
        }
        
        for category in self.analysis_framework.keys():
            if category in analysis_a and category in analysis_b:
                comparison = self.compare_category(
                    category, 
                    analysis_a[category], 
                    analysis_b[category]
                )
                report["詳細分析"][category] = comparison
        
        report["摘要"] = self.generate_executive_summary(report["詳細分析"])
        report["綜合評估"] = self.generate_overall_assessment(analysis_a, analysis_b)
        
        return report
    
    def compare_category(self, category, analysis_a, analysis_b):
        if analysis_a.get("status") != "已分析" or analysis_b.get("status") != "已分析":
            return {
                "比較結果": f"資料不足，無法比較。報告A狀態: {analysis_a.get('status')}，報告B狀態: {analysis_b.get('status')}",
                "報告A狀態": analysis_a.get("status", "未知"),
                "報告B狀態": analysis_b.get("status", "未知")
            }
        
        prompt = f"""請比較以下兩份台積電財報的{category}：

報告A的{category}分析：
{analysis_a.get('analysis', '無資料')}

報告B的{category}分析：
{analysis_b.get('analysis', '無資料')}

請提供詳細比較（請用繁體中文）：
1. 主要數據差異（具體數字比較）
2. 趨勢變化分析
3. 優劣勢評估
4. 關鍵發現

格式簡潔清楚。"""

        comparison_result = self.qa_engine.generate_answer(prompt, temperature=0.1)
        
        return {
            "比較結果": comparison_result,
            "資料品質": {
                "報告A": analysis_a.get("data_quality", "未知"),
                "報告B": analysis_b.get("data_quality", "未知")
            },
            "分析片段數": {
                "報告A": analysis_a.get("sections_analyzed", 0),
                "報告B": analysis_b.get("sections_analyzed", 0)
            }
        }
    
    def generate_executive_summary(self, detailed_analysis):
        successful_analyses = {k: v for k, v in detailed_analysis.items() 
                             if "比較結果" in v and len(v["比較結果"]) > 50}
        
        key_findings = []
        for category, analysis in successful_analyses.items():
            finding = analysis["比較結果"]
            if len(finding) > 200:
                finding = finding[:200] + "..."
            key_findings.append(f"{category}: {finding}")
        
        coverage_rate = f"{len(successful_analyses)}/{len(self.analysis_framework)} ({len(successful_analyses)/len(self.analysis_framework)*100:.1f}%)"
        
        return {
            "關鍵發現": key_findings[:5],
            "資料覆蓋率": coverage_rate,
            "分析完整度": "高" if len(successful_analyses) >= 4 else "中" if len(successful_analyses) >= 2 else "低"
        }
    
    def generate_overall_assessment(self, analysis_a, analysis_b):
        successful_a = sum(1 for v in analysis_a.values() if v.get("status") == "已分析")
        successful_b = sum(1 for v in analysis_b.values() if v.get("status") == "已分析")
        total_categories = len(self.analysis_framework)
        
        return {
            "分析完整度": {
                "報告A": f"{successful_a}/{total_categories} ({successful_a/total_categories*100:.1f}%)",
                "報告B": f"{successful_b}/{total_categories} ({successful_b/total_categories*100:.1f}%)"
            },
            "建議": [
                "建議檢視財務數據的一致性",
                "關注關鍵指標的變化趨勢",
                "評估投資決策的風險因子"
            ],
            "分析方法": "AI智能語義分析"
        }
    
    def format_report_as_markdown(self, report):
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