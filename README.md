# 財報比較分析AI Agent

## 專案目的
比較分析兩份PDF財報文件，範例使用台積電財報。目前還在修正階段。

## 功能
- PDF文件解析
- 基本財報比較分析  
- 簡單問答功能

## 環境
- Ubuntu 24.04.2 LTS
- Python 3.8+
- Ollama + LLaMA 3

## 安裝
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
##  使用
```
python app.py --mode analysis
python app.py --mode chat
```
### 指令
help          # 顯示幫助
save          # 儲存當前對話
load          # 載入歷史對話
clear         # 清除對話歷史
quit          # 退出系統
