import os
import re
import io
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import fitz  # PyMuPDF
from collections import defaultdict
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
    # 設定Tesseract路徑 (WSL/Ubuntu)
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

class FinancialTableAgent:
    
    def __init__(self):
        self.table_patterns = {
            # 投資明細表格模式
            'investment_table': {
                'keywords': ['投資', '持有', '證券', '公司', '股數', '金額', '公允價值'],
                'structure_indicators': ['TSMC', 'USD', '%', '股', '仟元', '萬元']
            },
            # 損益表模式
            'income_statement': {
                'keywords': ['營業收入', '營業成本', '毛利', '淨利', '稅前'],
                'structure_indicators': ['千元', '年度', '本期', '去年同期']
            },
            # 資產負債表模式
            'balance_sheet': {
                'keywords': ['資產', '負債', '權益', '流動', '非流動'],
                'structure_indicators': ['總計', '合計', '小計']
            },
            # 現金流量表模式
            'cash_flow': {
                'keywords': ['現金流量', '營業活動', '投資活動', '融資活動'],
                'structure_indicators': ['流入', '流出', '淨額']
            }
        }
        
        # OCR配置
        self.ocr_configs = {
            'high_accuracy': r'--oem 3 --psm 6 -l chi_tra+eng',
            'table_structure': r'--oem 3 --psm 4 -l chi_tra+eng',
            'dense_text': r'--oem 3 --psm 11 -l chi_tra+eng',
            'sparse_text': r'--oem 3 --psm 8 -l chi_tra+eng'
        }
    
    def extract_text_from_pdf(self, pdf_path, output_path=None):
        """AI Agent主要處理流程"""
        logger.info(f"🤖 財報表格AI Agent啟動: {os.path.basename(pdf_path)}")
        
        # 檢查工具可用性
        self._check_dependencies()
        
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            # Agent處理統計
            agent_stats = {
                'total_pages': total_pages,
                'table_pages': 0,
                'ocr_pages': 0,
                'hybrid_pages': 0,
                'failed_pages': 0,
                'financial_tables_found': 0
            }
            
            extracted_content = []
            financial_data = defaultdict(list)
            
            print(f"開始處理 {total_pages} 頁財報")
            
            for page_num in range(total_pages):
                page = doc[page_num]
                
                # AI頁面智能分析
                page_analysis = self._ai_analyze_page(page, page_num)
                
                # 根據分析結果選擇最佳處理策略
                processing_result = self._process_page_with_ai(page, page_num, page_analysis)
                
                # 更新統計
                agent_stats[f"{processing_result['method']}_pages"] += 1
                if processing_result['is_financial_table']:
                    agent_stats['financial_tables_found'] += 1
                
                # 提取財務數據
                if processing_result['content']:
                    extracted_financial = self._extract_financial_data(
                        processing_result['content'], page_num + 1
                    )
                    if extracted_financial:
                        for category, data in extracted_financial.items():
                            financial_data[category].extend(data)
                
                # 格式化頁面內容
                formatted_page = self._format_agent_page(
                    processing_result, page_num + 1, page_analysis
                )
                extracted_content.append(formatted_page)
                
                # 進度顯示
                if (page_num + 1) % 10 == 0:
                    print(f"✅ 已處理 {page_num + 1}/{total_pages} 頁")
            
            doc.close()
            
            final_report = self._generate_agent_report(
                extracted_content, financial_data, agent_stats
            )
            
            if output_path:
                self._save_agent_report(final_report, output_path)
            
            print(f"AI Agent處理完成！")
            self._print_agent_summary(agent_stats)
            
            return final_report
            
        except Exception as e:
            logger.error(f"AI Agent處理失敗: {e}")
            raise Exception(f"財報AI Agent錯誤: {e}")
    
    def _check_dependencies(self):
        """檢查依賴工具"""
        tools_status = []
        
        if TESSERACT_AVAILABLE:
            try:
                test_result = pytesseract.get_tesseract_version()
                tools_status.append(f"Tesseract {test_result}")
            except Exception:
                tools_status.append("Tesseract配置錯誤")
        else:
            tools_status.append("Tesseract未安裝")
        
        if PDFPLUMBER_AVAILABLE:
            tools_status.append("pdfplumber可用")
        else:
            tools_status.append("pdfplumber未安裝")
        
        tools_status.append("PyMuPDF可用")
        tools_status.append("OpenCV可用")
        
        print("🔧 AI Agent工具檢查:")
        for status in tools_status:
            print(f"   {status}")
        print()
    
    def _ai_analyze_page(self, page, page_num):
        """AI智能頁面分析"""
        try:
            # 多重分析策略
            text_analysis = self._analyze_text_content(page)
            structure_analysis = self._analyze_page_structure(page)
            visual_analysis = self._analyze_visual_features(page)
            
            # AI決策邏輯
            analysis_result = {
                'page_num': page_num + 1,
                'content_type': self._determine_content_type(text_analysis, structure_analysis),
                'complexity_level': self._assess_complexity(text_analysis, structure_analysis, visual_analysis),
                'table_type': self._identify_table_type(text_analysis),
                'recommended_strategy': None,
                'confidence': 0.0
            }
            
            # AI推薦處理策略
            analysis_result['recommended_strategy'] = self._ai_recommend_strategy(analysis_result)
            
            return analysis_result
            
        except Exception as e:
            logger.warning(f"頁面分析失敗 {page_num + 1}: {e}")
            return {
                'page_num': page_num + 1,
                'content_type': 'unknown',
                'complexity_level': 'medium',
                'recommended_strategy': 'fallback'
            }
    
    def _analyze_text_content(self, page):
        text = page.get_text()
        
        # 計算各種特徵
        char_count = len(text)
        line_count = len(text.split('\n'))
        
        # 財務關鍵詞密度
        financial_keywords = 0
        for pattern_name, pattern_info in self.table_patterns.items():
            for keyword in pattern_info['keywords']:
                financial_keywords += text.lower().count(keyword.lower())
        
        # 數字密度
        numbers = re.findall(r'\d{1,3}(?:,\d{3})*(?:\.\d+)?', text)
        number_density = len(numbers) / max(char_count, 1) * 1000
        
        # 結構指標
        structure_indicators = 0
        for pattern_name, pattern_info in self.table_patterns.items():
            for indicator in pattern_info['structure_indicators']:
                structure_indicators += text.count(indicator)
        
        return {
            'char_count': char_count,
            'line_count': line_count,
            'financial_keywords': financial_keywords,
            'number_density': number_density,
            'structure_indicators': structure_indicators,
            'has_substantial_content': char_count > 100
        }
    
    def _analyze_page_structure(self, page):
        try:
            text_dict = page.get_text("dict")
            
            blocks_count = len(text_dict.get("blocks", []))
            
            font_sizes = []
            positions = []
            
            for block in text_dict.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            font_sizes.append(span.get("size", 12))
                            positions.append(span["bbox"])
            
            font_variance = np.var(font_sizes) if font_sizes else 0
            
            return {
                'blocks_count': blocks_count,
                'font_variance': font_variance,
                'has_structured_layout': blocks_count > 5 and font_variance > 2,
                'has_table_structure': self._detect_table_structure(text_dict)
            }
            
        except Exception:
            return {
                'blocks_count': 0,
                'has_structured_layout': False,
                'has_table_structure': False
            }
    
    def _detect_table_structure(self, text_dict):
        aligned_blocks = 0
        total_blocks = 0
        
        for block in text_dict.get("blocks", []):
            if "lines" in block:
                total_blocks += 1
                line_positions = []
                for line in block["lines"]:
                    if line["spans"]:
                        line_positions.append(line["spans"][0]["bbox"][0])
                
                if len(set(line_positions)) < len(line_positions) * 0.8:
                    aligned_blocks += 1
        
        return aligned_blocks / max(total_blocks, 1) > 0.3
    
    def _analyze_visual_features(self, page):
        try:
            mat = fitz.Matrix(1.5, 1.5)  # 中等解析度
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            image = Image.open(io.BytesIO(img_data))
            
            gray_image = image.convert('L')
            img_array = np.array(gray_image)
            
            edges = cv2.Canny(img_array, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=100, maxLineGap=10)
            
            line_count = len(lines) if lines is not None else 0
            
            text_density = np.sum(img_array < 200) / img_array.size
            
            return {
                'has_lines': line_count > 10,
                'line_count': line_count,
                'text_density': text_density,
                'is_mostly_text': text_density > 0.1
            }
            
        except Exception:
            return {
                'has_lines': False,
                'line_count': 0,
                'text_density': 0,
                'is_mostly_text': False
            }
    
    def _determine_content_type(self, text_analysis, structure_analysis):
        if text_analysis['financial_keywords'] > 5 and structure_analysis['has_table_structure']:
            return 'complex_financial_table'
        elif text_analysis['financial_keywords'] > 2:
            return 'financial_content'
        elif structure_analysis['has_structured_layout']:
            return 'structured_text'
        elif text_analysis['has_substantial_content']:
            return 'plain_text'
        else:
            return 'minimal_content'
    
    def _assess_complexity(self, text_analysis, structure_analysis, visual_analysis):
        """評估複雜度"""
        complexity_score = 0
        
        # 文字複雜度
        if text_analysis['number_density'] > 10:
            complexity_score += 2
        if text_analysis['financial_keywords'] > 5:
            complexity_score += 2
        
        # 結構複雜度
        if structure_analysis['has_table_structure']:
            complexity_score += 2
        if structure_analysis['font_variance'] > 5:
            complexity_score += 1
        
        # 視覺複雜度
        if visual_analysis['line_count'] > 20:
            complexity_score += 2
        
        if complexity_score >= 6:
            return 'high'
        elif complexity_score >= 3:
            return 'medium'
        else:
            return 'low'
    
    def _identify_table_type(self, text_analysis):
        text = str(text_analysis)  # 簡化版本，實際應該傳入原始文字
        
        for table_type, pattern_info in self.table_patterns.items():
            score = 0
            for keyword in pattern_info['keywords']:
                if keyword in text.lower():
                    score += 1
            
            if score >= 2:
                return table_type
        
        return 'unknown'
    
    def _ai_recommend_strategy(self, analysis_result):
        content_type = analysis_result['content_type']
        complexity = analysis_result['complexity_level']
        
        if content_type == 'complex_financial_table':
            if TESSERACT_AVAILABLE:
                return 'ocr_enhanced'
            else:
                return 'hybrid'
        elif content_type == 'financial_content':
            if complexity == 'high':
                return 'hybrid'
            else:
                return 'text_extraction'
        elif content_type == 'structured_text':
            return 'structured_extraction'
        else:
            return 'basic_extraction'
    
    def _process_page_with_ai(self, page, page_num, analysis):
        strategy = analysis['recommended_strategy']
        
        try:
            if strategy == 'ocr_enhanced':
                content = self._process_with_ocr_enhanced(page)
                method = 'ocr'
            elif strategy == 'hybrid':
                content = self._process_with_hybrid_method(page)
                method = 'hybrid'
            elif strategy == 'structured_extraction':
                content = self._process_with_structured_extraction(page)
                method = 'table'
            else:
                content = self._process_with_basic_extraction(page)
                method = 'table'
            
            return {
                'content': content,
                'method': method,
                'strategy': strategy,
                'is_financial_table': analysis['content_type'] == 'complex_financial_table',
                'success': bool(content and len(content) > 50)
            }
            
        except Exception as e:
            logger.warning(f"處理頁面 {page_num + 1} 失敗: {e}")
            return {
                'content': f"第 {page_num + 1} 頁處理失敗: {e}",
                'method': 'failed',
                'strategy': 'fallback',
                'is_financial_table': False,
                'success': False
            }
    
    def _process_with_ocr_enhanced(self, page):
        if not TESSERACT_AVAILABLE:
            return self._process_with_basic_extraction(page)
        
        try:
            mat = fitz.Matrix(3.0, 3.0)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            image = Image.open(io.BytesIO(img_data))
            enhanced_image = self._enhance_for_table_ocr(image)
            
            ocr_results = []
            
            for config_name, config in self.ocr_configs.items():
                try:
                    result = pytesseract.image_to_string(
                        enhanced_image, 
                        config=config,
                        lang='chi_tra+eng'
                    )
                    if result and len(result.strip()) > 100:
                        ocr_results.append((config_name, result))
                except Exception:
                    continue
            
            if ocr_results:
                best_result = max(ocr_results, key=lambda x: len(x[1]))
                processed_text = self._post_process_ocr_result(best_result[1])
                return self._reconstruct_table_from_ocr(processed_text)
            
            return self._process_with_basic_extraction(page)
            
        except Exception as e:
            logger.warning(f"OCR增強處理失敗: {e}")
            return self._process_with_basic_extraction(page)
    
    def _enhance_for_table_ocr(self, image):
        try:
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            denoised = cv2.fastNlMeansDenoising(gray)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(enhanced, -1, kernel)
            
            binary = cv2.adaptiveThreshold(sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
            
            return Image.fromarray(binary)
            
        except Exception:
            return image
    
    def _post_process_ocr_result(self, text):
        if not text:
            return ""
        
        corrections = {
            'o': '0', 'O': '0', '○': '0',
            'l': '1', 'I': '1', '|': '1',
            'S': '5', 's': '5',
            'G': '6', 'g': '6',
            'B': '8',
            '，': ',', '。': '.', '％': '%',
            '（': '(', '）': ')',
            '台積霞': '台積電',
            'TSMC.*?lobal': 'TSMC Global',
        }
        
        corrected_text = text
        for wrong, correct in corrections.items():
            if len(wrong) == 1:  # 單字符修正
                corrected_text = re.sub(f'(\\d){re.escape(wrong)}(\\d)', f'\\1{correct}\\2', corrected_text)
            else:  
                corrected_text = re.sub(wrong, correct, corrected_text, flags=re.IGNORECASE)
        
        return corrected_text
    
    def _reconstruct_table_from_ocr(self, text):
        if not text:
            return ""
        
        lines = text.split('\n')
        reconstructed_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 檢查是否為表格行
            if self._is_table_row(line):
                formatted_line = self._format_table_row(line)
                reconstructed_lines.append(formatted_line)
            else:
                reconstructed_lines.append(line)
        
        return '\n'.join(reconstructed_lines)
    
    def _is_table_row(self, line):
        has_numbers = bool(re.search(r'\d', line))
        has_separators = bool(re.search(r'[|\t]|  {2,}', line))
        has_financial_indicators = bool(re.search(r'USD|TWD|NT\$|%|股|萬|億', line))
        
        return has_numbers and (has_separators or has_financial_indicators)
    
    def _format_table_row(self, line):
        parts = re.split(r'  {2,}|\t+', line)
        if len(parts) > 1:
            cleaned_parts = [part.strip() for part in parts if part.strip()]
            return ' | '.join(cleaned_parts)
        
        return line
    
    def _process_with_hybrid_method(self, page):
        results = []
        
        basic_text = page.get_text()
        if basic_text:
            results.append("=== 基本文字提取 ===")
            results.append(self._clean_basic_text(basic_text))
        
        try:
            structured_text = self._extract_structured_layout(page)
            if structured_text and len(structured_text) > 100:
                results.append("=== 結構化提取 ===")
                results.append(structured_text)
        except Exception:
            pass
        
        if TESSERACT_AVAILABLE and sum(len(r) for r in results) < 500:
            try:
                ocr_text = self._simple_ocr_extract(page)
                if ocr_text and len(ocr_text) > 100:
                    results.append("=== OCR補充 ===")
                    results.append(ocr_text)
            except Exception:
                pass
        
        return '\n\n'.join(results) if results else "混合處理失敗"
    
    def _extract_structured_layout(self, page):
        try:
            text_dict = page.get_text("dict")
            
            elements = []
            for block in text_dict.get("blocks", []):
                if "lines" not in block:
                    continue
                
                for line in block["lines"]:
                    line_elements = []
                    for span in line["spans"]:
                        if span["text"].strip():
                            line_elements.append({
                                "text": span["text"].strip(),
                                "x": span["bbox"][0],
                                "y": span["bbox"][1]
                            })
                    
                    if line_elements:
                        line_elements.sort(key=lambda x: x["x"])
                        elements.append({
                            "y": line_elements[0]["y"],
                            "elements": line_elements
                        })
            
            elements.sort(key=lambda x: x["y"])
            
            structured_lines = []
            for line_data in elements:
                line_text = self._format_line_with_spacing(line_data["elements"])
                if line_text.strip():
                    structured_lines.append(line_text)
            
            return '\n'.join(structured_lines)
            
        except Exception:
            return ""
    
    def _format_line_with_spacing(self, elements):
        if not elements:
            return ""
        
        formatted_parts = []
        last_x = 0
        
        for elem in elements:
            current_x = elem["x"]
            gap = current_x - last_x
            
            if last_x > 0:
                if gap > 120:
                    formatted_parts.append(" | ")
                elif gap > 60:
                    formatted_parts.append(" | ")
                elif gap > 20:
                    formatted_parts.append("  ")
                elif gap > 8:
                    formatted_parts.append(" ")
            
            formatted_parts.append(elem["text"])
            last_x = current_x + len(elem["text"]) * 6
        
        return "".join(formatted_parts)
    
    def _simple_ocr_extract(self, page):
        try:
            mat = fitz.Matrix(2.0, 2.0)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            image = Image.open(io.BytesIO(img_data))
            
            result = pytesseract.image_to_string(
                image,
                config=self.ocr_configs['high_accuracy'],
                lang='chi_tra+eng'
            )
            
            return self._post_process_ocr_result(result)
            
        except Exception:
            return ""
    
    def _process_with_structured_extraction(self, page):
        return self._extract_structured_layout(page)
    
    def _process_with_basic_extraction(self, page):
        return self._clean_basic_text(page.get_text())
    
    def _clean_basic_text(self, text):
        if not text:
            return ""
        
        text = re.sub(r'(\d)\s+([,，])\s*(\d)', r'\1\2\3', text)
        text = re.sub(r'(\d)\s+([.])\s*(\d)', r'\1\2\3', text)
        text = re.sub(r'(\d)\s*([%％])', r'\1\2', text)
        text = re.sub(r'([\$＄])\s+(\d)', r'\1\2', text)
        
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        return text.strip()
    
    def _extract_financial_data(self, content, page_num):
        financial_data = defaultdict(list)
        
        if not content:
            return financial_data
        
        patterns = {
            'revenue': [
                r'營業收入[淨]?[：:\s]*[NT\$]?\s*(\d{1,3}(?:,\d{3})*)',
                r'revenue[：:\s]*[NT\$]?\s*(\d{1,3}(?:,\d{3})*)',
                r'淨營業收入[：:\s]*[NT\$]?\s*(\d{1,3}(?:,\d{3})*)'
            ],
            'net_income': [
                r'淨利[潤]?[：:\s]*[NT\$]?\s*(\d{1,3}(?:,\d{3})*)',
                r'本期淨利[：:\s]*[NT\$]?\s*(\d{1,3}(?:,\d{3})*)',
                r'net\s+income[：:\s]*[NT\$]?\s*(\d{1,3}(?:,\d{3})*)'
            ],
            'total_assets': [
                r'資產總額[：:\s]*[NT\$]?\s*(\d{1,3}(?:,\d{3})*)',
                r'總資產[：:\s]*[NT\$]?\s*(\d{1,3}(?:,\d{3})*)',
                r'total\s+assets[：:\s]*[NT\$]?\s*(\d{1,3}(?:,\d{3})*)'
            ]
        }
        
        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    try:
                        value_str = match.group(1).replace(',', '')
                        value = float(value_str)
                        financial_data[category].append({
                            'value': value,
                            'page': page_num,
                            'context': match.group(0)
                        })
                    except ValueError:
                        continue
        
        return financial_data
    
    def _format_agent_page(self, processing_result, page_num, analysis):
        """格式化Agent頁面輸出"""
        header_parts = [
            f"第 {page_num} 頁",
            f"[{analysis['content_type']}]",
            f"複雜度: {analysis['complexity_level']}",
            f"策略: {processing_result['strategy']}"
        ]
        
        if processing_result['is_financial_table']:
            header_parts.append("表格")
        
        if processing_result['success']:
            header_parts.append("ok")
        else:
            header_parts.append("!")
        
        header = " - ".join(header_parts)
        content = processing_result['content']
        
        return f"\n{'='*80}\n{header}\n{'='*80}\n{content}"
    
    def _generate_agent_report(self, extracted_content, financial_data, agent_stats):
        report_parts = []
        
        report_parts.append("=" * 100)
        report_parts.append("財報表格處理AI Agent - 完整分析報告")
        report_parts.append("=" * 100)
        
        report_parts.append(f"\n統計:")
        report_parts.append(f"  總頁數: {agent_stats['total_pages']}")
        report_parts.append(f"  表格頁: {agent_stats['table_pages']}")
        report_parts.append(f"  OCR頁: {agent_stats['ocr_pages']}")
        report_parts.append(f"  混合頁: {agent_stats['hybrid_pages']}")
        report_parts.append(f"  失敗頁: {agent_stats['failed_pages']}")
        report_parts.append(f"  財務表格: {agent_stats['financial_tables_found']} 個")
        
        success_rate = (agent_stats['total_pages'] - agent_stats['failed_pages']) / agent_stats['total_pages'] * 100
        report_parts.append(f"  成功率: {success_rate:.1f}%")
        
        if financial_data:
            report_parts.append(f"\nAI提取的財務數據:")
            for category, data_list in financial_data.items():
                if data_list:
                    unique_values = len(set(item['value'] for item in data_list))
                    report_parts.append(f"  {category}: {len(data_list)} 個數據點 ({unique_values} 個唯一值)")
        
        # 完整內容
        report_parts.append(f"\nAI Agent完整處理結果:")
        report_parts.extend(extracted_content)
        
        return '\n'.join(report_parts)
    
    def _save_agent_report(self, report, output_path):
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            logger.info(f"報告已儲存: {output_path}")
            
        except Exception as e:
            logger.error(f"儲存失敗: {e}")
    
    def _print_agent_summary(self, stats):
        print(f"\nAI Agent處理摘要:")
        print(f"智能策略選擇")
        print(f"成功處理: {stats['total_pages'] - stats['failed_pages']}/{stats['total_pages']} 頁")
        print(f"財務表格發現: {stats['financial_tables_found']} 個")
        print(f"OCR增強: {stats['ocr_pages']} 頁")
        print(f"混合處理: {stats['hybrid_pages']} 頁")
        
        if TESSERACT_AVAILABLE:
            print(f"OCR引擎: 可用")
        else:
            print(f"OCR引擎: 不可用")
    
    def process_reports(self, report_a_path, report_b_path, output_dir="outputs"):
        results = {}
        
        print("啟動")
        print("=" * 60)
        
        try:
            # 處理報告A
            print(f"\n處理財報A: {os.path.basename(report_a_path)}")
            output_a = os.path.join(output_dir, "report_a_agent.txt")
            text_a = self.extract_text_from_pdf(report_a_path, output_a)
            results['report_a'] = text_a
            
            # 處理報告B
            print(f"\n處理財報B: {os.path.basename(report_b_path)}")
            output_b = os.path.join(output_dir, "report_b_agent.txt")
            text_b = self.extract_text_from_pdf(report_b_path, output_b)
            results['report_b'] = text_b
            
            print(f"\n完成！")
            print(f"   結果文件: {output_dir}/report_*_agent.txt")
            
            return results
            
        except Exception as e:
            logger.error(f"AI Agent任務失敗: {e}")
            raise


class PDFParser(FinancialTableAgent):
    pass