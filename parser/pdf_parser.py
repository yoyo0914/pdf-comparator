"""
PDF解析器
"""
import os
import fitz
from PIL import Image
import pytesseract
import io
import logging
import re

# 嘗試導入進階表格解析庫
try:
    import camelot
    import tabula
    import pandas as pd
    import warnings
    # 隱藏所有警告
    warnings.filterwarnings('ignore')
    import os
    # 隱藏Java輸出
    os.environ['JAVA_TOOL_OPTIONS'] = '-Dfile.encoding=UTF-8 -Djava.awt.headless=true'
    ADVANCED_MODE = True
except ImportError:
    ADVANCED_MODE = False

class PDFParser:
    def __init__(self, tesseract_cmd=None):
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        logging.getLogger(__name__).setLevel(logging.WARNING)
        
    def extract_text_from_pdf(self, pdf_path, output_path=None):
        try:
            doc = fitz.open(pdf_path)
            extracted_text = []
            total_pages = len(doc)
            
            print(f"解析 {total_pages} 頁...", end="", flush=True)
            
            for page_num in range(total_pages):
                # 簡單進度顯示
                if page_num % 20 == 0 and page_num > 0:
                    print(f" {page_num}", end="", flush=True)
                elif page_num % 5 == 0:
                    print(".", end="", flush=True)
                
                page = doc.load_page(page_num)
                
                # 只對可能有表格的頁面嘗試進階解析
                if ADVANCED_MODE and self._might_have_tables(page):
                    page_content = self._extract_with_tables(pdf_path, page_num, page)
                else:
                    page_content = self._extract_basic(page)
                
                extracted_text.append(f"\n第 {page_num + 1} 頁\n" + "="*50 + "\n")
                extracted_text.append(page_content)
            
            print(" 完成")
            doc.close()
            
            full_text = "\n".join(extracted_text)
            cleaned_text = self._clean_text(full_text)
            
            if output_path:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_text)
            
            return cleaned_text
            
        except Exception as e:
            print(f" 失敗")
            raise Exception(f"PDF處理錯誤: {str(e)}")
    
    def _extract_with_tables(self, pdf_path, page_num, page):
        basic_text = self._extract_basic(page)
        tables = self._extract_tables(pdf_path, page_num + 1)
        
        if tables:
            content = [basic_text]
            for i, table in enumerate(tables):
                table_text = self._format_table(table, i)
                content.append(table_text)
            return "\n\n".join(content)
        
        return basic_text
    
    def _extract_tables(self, pdf_path, page_num):
        tables = []
        
        # 快速嘗試Camelot，限制時間
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                camelot_tables = camelot.read_pdf(
                    pdf_path, 
                    pages=str(page_num), 
                    flavor='lattice',
                    suppress_stdout=True,
                    suppress_stderr=True
                )
                
                for table in camelot_tables:
                    if table.df is not None and not table.df.empty and len(table.df) > 1:
                        df = self._clean_dataframe(table.df)
                        if not df.empty:
                            tables.append(df)
                            break  # 只取第一個有效表格
        except:
            pass
        
        # 如果Camelot沒找到表格，快速嘗試Tabula
        if not tables:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    tabula_tables = tabula.read_pdf(
                        pdf_path, 
                        pages=page_num, 
                        multiple_tables=False,  # 只取一個表格
                        pandas_options={'header': None},
                        silent=True
                    )
                    
                    if isinstance(tabula_tables, list) and tabula_tables:
                        df = tabula_tables[0]
                        if df is not None and not df.empty and len(df) > 1:
                            df = self._clean_dataframe(df)
                            if not df.empty:
                                tables.append(df)
            except:
                pass
        
        return tables[:1]  # 最多返回1個表格
    
    def _clean_dataframe(self, df):
        df = df.dropna(how='all').dropna(axis=1, how='all')
        df = df.fillna('')
        
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].str.replace('\n', ' ')
        
        if df.shape[0] < 2 or df.shape[1] < 2:
            return pd.DataFrame()
        
        return df
    
    def _format_table(self, df, table_index):
        if df.empty:
            return ""
        
        lines = [f"\n表格 {table_index + 1}"]
        lines.append("-" * 60)
        
        max_width = 20
        col_widths = []
        
        for col in df.columns:
            max_len = max(len(str(col)), df[col].astype(str).str.len().max() if not df[col].empty else 0)
            col_widths.append(min(max_len + 2, max_width))
        
        # 表頭
        header_parts = []
        for i, col in enumerate(df.columns):
            width = col_widths[i]
            header_parts.append(str(col)[:width-2].ljust(width))
        lines.append(" | ".join(header_parts))
        lines.append("-" * 60)
        
        # 數據行
        for idx, row in df.iterrows():
            row_parts = []
            for i, (col, value) in enumerate(row.items()):
                width = col_widths[i]
                cell_value = str(value)[:width-2].ljust(width)
                row_parts.append(cell_value)
            lines.append(" | ".join(row_parts))
        
        lines.append("-" * 60)
        return "\n".join(lines)
    
    def _extract_basic(self, page):
        try:
            text_dict = page.get_text("dict")
            lines = []
            
            for block in text_dict["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        line_text = ""
                        spans = []
                        
                        for span in line["spans"]:
                            text = span["text"].strip()
                            if text:
                                spans.append({"text": text, "bbox": span["bbox"]})
                        
                        if spans:
                            spans.sort(key=lambda x: x["bbox"][0])
                            line_parts = []
                            last_right = 0
                            
                            for span in spans:
                                left = span["bbox"][0]
                                if last_right > 0 and left - last_right > 20:
                                    if left - last_right > 50:
                                        line_parts.append("\t")
                                    else:
                                        line_parts.append(" ")
                                
                                line_parts.append(span["text"])
                                last_right = span["bbox"][2]
                            
                            line_text = "".join(line_parts)
                            lines.append({"text": line_text, "y": line["bbox"][1]})
            
            lines.sort(key=lambda x: x["y"])
            combined_text = "\n".join([line["text"] for line in lines])
            
            if len(combined_text.strip()) < 100:
                ocr_text = self._ocr_page(page)
                if ocr_text.strip():
                    return ocr_text
            
            return combined_text
            
        except Exception:
            return page.get_text()
    
    def _ocr_page(self, page):
        try:
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            image = Image.open(io.BytesIO(img_data))
            if image.mode != 'L':
                image = image.convert('L')
            
            custom_config = r'--oem 3 --psm 6 -l chi_tra+eng'
            ocr_text = pytesseract.image_to_string(image, config=custom_config)
            
            return ocr_text
            
        except Exception:
            return ""
    
    def _clean_text(self, text):
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
        text = re.sub(r'\s+([，。！？；：])', r'\1', text)
        text = re.sub(r'(\d)\s*,\s*(\d)', r'\1,\2', text)
        text = re.sub(r'(\d)\s*\.\s*(\d)', r'\1.\2', text)
        return text.strip()
    
    def _might_have_tables(self, page):
        """快速判斷頁面是否可能包含表格"""
        try:
            # 獲取基本文字
            text = page.get_text()
            
            # 簡單啟發式判斷
            has_numbers = len([c for c in text if c.isdigit()]) > 10
            has_currency = any(symbol in text for symbol in ["$", "元", "萬", "億", "%"])
            has_table_words = any(word in text for word in ["項目", "金額", "比例", "公司", "投資"])
            
            return has_numbers and (has_currency or has_table_words)
        except:
            return False
    
    def process_reports(self, report_a_path, report_b_path, output_dir="outputs"):
        results = {}
        
        print("處理財報A...", end=" ")
        output_a = os.path.join(output_dir, "report_a_text.txt")
        text_a = self.extract_text_from_pdf(report_a_path, output_a)
        results['report_a'] = text_a
        
        print("處理財報B...", end=" ")
        output_b = os.path.join(output_dir, "report_b_text.txt")
        text_b = self.extract_text_from_pdf(report_b_path, output_b)
        results['report_b'] = text_b
        
        return results