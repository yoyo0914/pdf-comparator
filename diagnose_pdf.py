"""
PDF提取品質診斷工具
"""
import re
import os

def diagnose_pdf_extraction_quality():
    """診斷PDF提取品質"""
    
    report_files = {
        'report_a': 'outputs/report_a_text.txt',
        'report_b': 'outputs/report_b_text.txt'
    }
    
    print("🔍 PDF提取品質診斷報告")
    print("=" * 60)
    
    for report_name, file_path in report_files.items():
        if not os.path.exists(file_path):
            print(f"❌ {report_name}: 文件不存在")
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"\n📄 {report_name.upper()} 診斷結果:")
        print("-" * 40)
        
        # 基本統計
        char_count = len(content)
        line_count = len(content.split('\n'))
        print(f"📊 文件大小: {char_count:,} 字符, {line_count:,} 行")
        
        # 年度識別檢查
        years_mentioned = diagnose_year_identification(content)
        print(f"📅 年度識別: {years_mentioned}")
        
        # 財務數據品質
        financial_data_quality = diagnose_financial_data(content)
        print(f"💰 財務數據品質: {financial_data_quality}")
        
        # 表格結構檢查
        table_quality = diagnose_table_structure(content)
        print(f"📋 表格結構: {table_quality}")
        
        # 頁面分類統計
        page_classification = diagnose_page_classification(content)
        print(f"📑 頁面分類: {page_classification}")
        
        # 內容示例（前1000字符）
        print(f"📝 內容示例:")
        clean_sample = content[:1000].replace('\n\n\n', '\n').strip()
        print(f"```\n{clean_sample}\n```")
        
        # 財務關鍵詞檢查
        keywords_found = diagnose_keywords(content)
        print(f"🔑 關鍵詞檢測: {keywords_found}")

def diagnose_year_identification(content):
    """診斷年度識別問題"""
    
    # 尋找各種年度格式
    patterns = {
        '民國年': r'民國\s*(\d{2,3})\s*年',
        '西元年': r'(20\d{2})\s*年',
        '年度標示': r'(\d{2,3})\s*年度',
        '期間標示': r'(\d{4})\s*年\s*\d+\s*月'
    }
    
    results = {}
    for pattern_name, pattern in patterns.items():
        matches = re.findall(pattern, content)
        if matches:
            unique_years = list(set(matches))
            results[pattern_name] = unique_years[:5]  # 最多顯示5個
    
    return results

def diagnose_financial_data(content):
    """診斷財務數據品質"""
    
    # 尋找財務數據模式
    financial_patterns = {
        '大金額': r'\$?\s*\d{1,3}(?:,\d{3}){2,}',  # 百萬以上金額
        '營收關鍵詞': r'營業收入|revenue|sales',
        '獲利關鍵詞': r'淨利|profit|net income',
        '資產關鍵詞': r'總資產|total assets|資產總額'
    }
    
    results = {}
    for category, pattern in financial_patterns.items():
        matches = re.findall(pattern, content, re.IGNORECASE)
        results[category] = len(matches)
    
    # 檢查數據完整性
    sample_numbers = re.findall(r'\$?\s*(\d{1,3}(?:,\d{3}){2,})', content)
    results['大金額樣本'] = sample_numbers[:3] if sample_numbers else ['無']
    
    return results

def diagnose_table_structure(content):
    """診斷表格結構品質"""
    
    lines = content.split('\n')
    
    # 統計表格特徵
    tab_lines = sum(1 for line in lines if '\t' in line)
    aligned_lines = sum(1 for line in lines if re.search(r'\s{4,}', line))
    table_headers = sum(1 for line in lines if re.search(r'項目|金額|年度|item|amount', line, re.IGNORECASE))
    
    # 檢查表格品質
    total_lines = len(lines)
    table_ratio = (tab_lines + aligned_lines) / total_lines if total_lines > 0 else 0
    
    quality_score = "優秀" if table_ratio > 0.3 else "良好" if table_ratio > 0.1 else "差"
    
    return {
        '制表符行數': tab_lines,
        '對齊行數': aligned_lines,
        '表格標題': table_headers,
        '表格比例': f"{table_ratio:.1%}",
        '品質評分': quality_score
    }

def diagnose_page_classification(content):
    """診斷頁面分類"""
    
    # 統計不同類型的頁面標記
    page_markers = re.findall(r'第\s*(\d+)\s*頁\s*\(([^)]+)\)', content)
    
    if not page_markers:
        return "無頁面分類標記"
    
    # 統計頁面類型
    page_types = {}
    for page_num, page_type in page_markers:
        page_types[page_type] = page_types.get(page_type, 0) + 1
    
    return page_types

def diagnose_keywords(content):
    """診斷關鍵詞覆蓋"""
    
    essential_keywords = {
        '台積電': r'台積電|TSMC|taiwan semiconductor',
        '營業收入': r'營業收入|revenue|sales',
        '淨利潤': r'淨利|net income|profit',
        '現金流': r'現金流|cash flow',
        '資產負債': r'資產|負債|assets|liabilities',
        '投資': r'投資|investment',
        '研發': r'研發|research|development|R&D'
    }
    
    results = {}
    for keyword, pattern in essential_keywords.items():
        matches = len(re.findall(pattern, content, re.IGNORECASE))
        results[keyword] = matches
    
    return results

def generate_improvement_suggestions():
    """生成改進建議"""
    
    print("\n💡 改進建議:")
    print("=" * 60)
    
    suggestions = [
        "1. 檢查PDF原始品質：是否為掃描版或圖片PDF",
        "2. 重新檢視表格提取邏輯：數字和標題的對應關係",
        "3. 加強年度識別：統一時間格式處理",
        "4. 改進財務數據匹配：確保數據和科目正確對應",
        "5. 優化頁面分類：不同類型頁面使用不同解析策略",
        "6. 增加數據驗證：檢查提取數據的合理性",
        "7. 考慮使用OCR：對複雜表格進行圖像識別"
    ]
    
    for suggestion in suggestions:
        print(f"   {suggestion}")
    
    print(f"\n🔧 建議執行順序：")
    print(f"   1. 先運行診斷工具查看具體問題")
    print(f"   2. 根據診斷結果針對性改進PDF解析器")
    print(f"   3. 重新解析並檢查品質")
    print(f"   4. 最後重新生成分析報告")

if __name__ == "__main__":
    diagnose_pdf_extraction_quality()
    generate_improvement_suggestions()