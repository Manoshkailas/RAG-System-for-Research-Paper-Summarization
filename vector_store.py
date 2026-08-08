import math
import re

class VectorStore:
    def __init__(self):
        self.chunks = []
        self.vocab = {}
        self.idf = {}

    def _tokenize(self, text):
        return re.findall(r'\b[a-z0-9]+\b', text.lower())

    def _update_index(self):
        if not self.chunks:
            return

        total_docs = len(self.chunks)
        doc_freq = {}
        unique_terms = set()

        for chunk in self.chunks:
            words = set(self._tokenize(chunk["text"]))
            for w in words:
                unique_terms.add(w)
                doc_freq[w] = doc_freq.get(w, 0) + 1

        self.vocab = {word: i for i, word in enumerate(sorted(unique_terms))}
        self.idf = {
            w: math.log((total_docs + 1) / (freq + 1)) + 1.0
            for w, freq in doc_freq.items()
        }

        for chunk in self.chunks:
            tokens = self._tokenize(chunk["text"])
            total_tokens = max(len(tokens), 1)
            tf = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1

            chunk["vector"] = {
                t: (count / total_tokens) * self.idf.get(t, 0)
                for t, count in tf.items()
            }

    def add_chunks(self, new_chunks):
        self.chunks.extend(new_chunks)
        self._update_index()

    def _cosine_sim(self, vec1, vec2):
        common = set(vec1.keys()).intersection(set(vec2.keys()))
        if not common:
            return 0.0

        dot = sum(vec1[k] * vec2[k] for k in common)
        norm1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        norm2 = math.sqrt(sum(v ** 2 for v in vec2.values()))

        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def search(self, query, paper_id=None, top_k=4):
        if not self.chunks:
            return []

        tokens = self._tokenize(query)
        if not tokens:
            return []

        total_tokens = len(tokens)
        query_tf = {}
        for t in tokens:
            query_tf[t] = query_tf.get(t, 0) + 1

        query_vec = {
            t: (count / total_tokens) * self.idf.get(t, 0)
            for t, count in query_tf.items()
            if t in self.idf
        }

        candidates = self.chunks
        if paper_id:
            candidates = [c for c in self.chunks if c["paper_id"] == paper_id]

        results = []
        for chunk in candidates:
            score = self._cosine_sim(query_vec, chunk.get("vector", {}))
            
            sec = chunk.get("section", "").lower()
            if any(t in sec for t in tokens):
                score += 0.15

            results.append({
                "chunk": chunk,
                "score": round(score, 4)
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def clear(self):
        self.chunks = []
        self.vocab = {}
        self.idf = {}
