# RAG-System-for-Research-Paper-Summarization
Retrival Augmented System specially developed to understand and summarize and answer the user queries from Research papers


## Key Features

 **PDF Section-Aware Ingestion**: Automatically extracts text and tags sections (Abstract, Introduction, Methodology, Results, Conclusion, References).
**Smart Vector Chunking & Retrieval**: In-memory TF-IDF + Cosine similarity vector store with metadata filtering (page numbers, section tags).
**Structured Academic Summaries**: Produces JSON/Markdown outputs categorized into Abstract, 3-5 Key Contributions, Methodology, Results, and Limitations.
**Interactive RAG Q&A**: Ask targeted questions about papers with citation snippets and relevance score tracking.
**Side-by-Side Paper Comparison**: Contrast two research papers simultaneously to evaluate architectural and benchmark differences.
**Explainability & Chunk Inspector**: Trace exactly which chunks and page numbers were retrieved to generate summaries or answers.
**FastAPI Web SPA**: Sleek glassmorphism dark-theme dashboard.
**Streamlit Dashboard**: Classic data science showcase layout.
**Multi-Provider & Offline Fallback**: Works with Google Gemini API, OpenAI API, and includes an offline local heuristic engine for zero-config demonstration.
## 2. Configure Environment Variables 

Copy `.env.example` to `.env` and insert your API keys:

```bash
cp .env.example .env
```

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
```

*(Note: If no API key is provided, ScholarRAG automatically uses its offline heuristic engine for seamless demo mode!)*

### 3. Generate a Sample Paper (Optional)

To quickly generate a test paper without downloading PDFs:

```bash
python sample_paper_generator.py sample_paper.pdf
```
