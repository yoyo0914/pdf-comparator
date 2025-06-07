# 財報比較分析AI Agent

## 專案目的
使用AI比較分析兩份PDF財報文件，範例使用台積電財報。目前還在開發階段。

## 功能
- PDF文件解析
- 基本財報比較分析  
- 簡單問答功能

## 環境需求
- WSL環境
- Python 3.8+
- Ollama + LLaMA 3

## 安裝

### 1. 安裝Ollama
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3
ollama serve