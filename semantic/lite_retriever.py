import re
import jieba
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class LiteSemanticRetriever:
    def __init__(self):
        self.chunks = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self.synonyms = {
            "營收": ["收入", "營業收入", "銷售收入", "revenue", "sales"],
            "獲利": ["盈利", "利潤", "淨利", "profit", "earnings"],
            "成長": ["增長", "增加", "growth", "increase"],
            "財務結構": ["資本結構", "financial structure"],
            "現金流": ["現金流量", "cash flow"],
            "投資": ["investment", "資本支出"],
            "風險": ["risk", "不確定性"]
        }
        
    def chunk_documents(self, report_a_text, report_b_text, chunk_size=500):
        def smart_chunk(text, report_id):
            paragraphs = text.split('\n\n')
            chunks = []
            current_chunk = ""
            
            for paragraph in paragraphs:
                if len(current_chunk) + len(paragraph) <= chunk_size:
                    current_chunk += paragraph + '\n\n'
                else:
                    if current_chunk.strip():
                        chunks.append({
                            'text': current_chunk.strip(),
                            'report_id': report_id,
                            'chunk_id': len(chunks)
                        })
                    current_chunk = paragraph + '\n\n'
            
            if current_chunk.strip():
                chunks.append({
                    'text': current_chunk.strip(),
                    'report_id': report_id,
                    'chunk_id': len(chunks)
                })
            return chunks
        
        chunks_a = smart_chunk(report_a_text, 'A')
        chunks_b = smart_chunk(report_b_text, 'B')
        self.chunks = chunks_a + chunks_b
        return self.chunks
    
    def build_index(self, force_rebuild=False):
        if not self.chunks:
            return
        
        texts = [self._expand_synonyms(chunk['text']) for chunk in self.chunks]
        self.vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
        self.tfidf_matrix = self.vectorizer.fit_transform(texts)
    
    def _expand_synonyms(self, text):
        expanded_text = text
        for key, synonyms in self.synonyms.items():
            for synonym in synonyms:
                if synonym in text:
                    expanded_text += f" {key}"
        return expanded_text
    
    def semantic_search(self, query, top_k=5, score_threshold=0.1):
        if self.vectorizer is None:
            return []
        
        expanded_query = self._expand_synonyms(query)
        query_vector = self.vectorizer.transform([expanded_query])
        similarities = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = similarities[idx]
            if score >= score_threshold:
                chunk = self.chunks[idx]
                results.append({
                    'text': chunk['text'],
                    'report_id': chunk['report_id'],
                    'chunk_id': chunk['chunk_id'],
                    'similarity_score': float(score),
                    'length': len(chunk['text'])
                })
        return results
    
    def smart_context_selection(self, query, max_tokens=15000):
        search_results = self.semantic_search(query, top_k=15)
        
        if not search_results:
            search_results = self._keyword_fallback(query)
        
        selected_chunks = []
        total_length = 0
        
        for result in search_results:
            chunk_length = len(result['text'])
            if total_length + chunk_length <= max_tokens:
                selected_chunks.append(result)
                total_length += chunk_length
            else:
                remaining_space = max_tokens - total_length
                if remaining_space > 200:
                    result['text'] = result['text'][:remaining_space-50] + "..."
                    selected_chunks.append(result)
                break
        
        context_parts = [f"報告{chunk['report_id']}\n{chunk['text']}" for chunk in selected_chunks]
        final_context = "\n\n".join(context_parts)
        return final_context, selected_chunks
    
    def _keyword_fallback(self, query):
        keywords = jieba.cut(query)
        results = []
        
        for chunk in self.chunks:
            score = 0
            text_lower = chunk['text'].lower()
            
            for keyword in keywords:
                if len(keyword) > 1:
                    score += text_lower.count(keyword.lower()) * 2
            
            numbers = re.findall(r'\d+', chunk['text'])
            score += len(numbers) * 0.1
            
            if score > 0:
                results.append({
                    'text': chunk['text'],
                    'report_id': chunk['report_id'],
                    'chunk_id': chunk['chunk_id'],
                    'similarity_score': score / 10,
                    'length': len(chunk['text'])
                })
        
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        return results[:10]
