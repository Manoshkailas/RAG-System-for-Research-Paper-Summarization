import os
import json
import shutil
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pydantic import BaseModel

import config
from pdf_parser import parse_paper
from vector_store import VectorStore
from rag_engine import RAGEngine

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Academic Paper Summariser")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vector_store = VectorStore()
rag_engine = RAGEngine(vector_store)
papers_db = {}

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

class QuerySchema(BaseModel):
    question: str
    paper_id: Optional[str] = None
    top_k: Optional[int] = 4

class CompareSchema(BaseModel):
    paper_id_a: str
    paper_id_b: str

class SummarizeSchema(BaseModel):
    paper_id: str

@app.get("/", response_class=HTMLResponse)
async def home():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h2>Paper Summariser API is running. Access <a href='/docs'>/docs</a> for API UI.</h2>")

@app.post("/api/upload")
async def upload_paper(file: UploadFile = File(...)):
    safe_filename = os.path.basename(file.filename or "document.pdf")
    if not safe_filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_path = os.path.join(config.UPLOAD_FOLDER, safe_filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        parsed = parse_paper(file_path, chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP)
        pid = parsed["paper_id"]

        vector_store.add_chunks(parsed["chunks"])

        papers_db[pid] = {
            "paper_id": pid,
            "title": parsed["title"],
            "filename": parsed["filename"],
            "total_pages": parsed["total_pages"],
            "total_chunks": parsed["total_chunks"],
            "file_path": file_path,
            "parsed_data": parsed
        }

        summary_data = rag_engine.summarize_paper(pid, papers_db[pid])
        papers_db[pid]["summary"] = summary_data["summary"]
        papers_db[pid]["retrieved_chunks"] = summary_data["retrieved_chunks"]

        return {
            "status": "success",
            "message": f"Successfully uploaded '{file.filename}'",
            "paper_id": pid,
            "title": parsed["title"],
            "total_pages": parsed["total_pages"],
            "total_chunks": parsed["total_chunks"],
            "summary": summary_data["summary"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

@app.get("/api/papers")
async def list_papers():
    paper_list = []
    for pid, p in papers_db.items():
        paper_list.append({
            "paper_id": pid,
            "title": p["title"],
            "filename": p["filename"],
            "total_pages": p["total_pages"],
            "total_chunks": p["total_chunks"],
            "has_summary": "summary" in p
        })
    return {"count": len(paper_list), "papers": paper_list}

@app.get("/api/papers/{paper_id}")
async def get_paper_details(paper_id: str):
    if paper_id not in papers_db:
        raise HTTPException(status_code=404, detail="Paper not found.")
    p = papers_db[paper_id]
    return {
        "paper_id": p["paper_id"],
        "title": p["title"],
        "filename": p["filename"],
        "total_pages": p["total_pages"],
        "total_chunks": p["total_chunks"],
        "summary": p.get("summary"),
        "retrieved_chunks": p.get("retrieved_chunks", [])
    }

@app.post("/api/summarize")
async def summarize(req: SummarizeSchema):
    if req.paper_id not in papers_db:
        raise HTTPException(status_code=404, detail="Paper not found.")

    paper_info = papers_db[req.paper_id]
    result = rag_engine.summarize_paper(req.paper_id, paper_info)
    paper_info["summary"] = result["summary"]
    return result

@app.post("/api/query")
async def query_paper(req: QuerySchema):
    if req.paper_id and req.paper_id not in papers_db:
        raise HTTPException(status_code=404, detail="Paper ID not found.")

    top_k = req.top_k or config.TOP_K_RESULTS
    return rag_engine.answer_question(req.question, paper_id=req.paper_id, top_k=top_k)

@app.post("/api/compare")
async def compare_two_papers(req: CompareSchema):
    if req.paper_id_a not in papers_db or req.paper_id_b not in papers_db:
        raise HTTPException(status_code=404, detail="One or both paper IDs not found.")

    pA = papers_db[req.paper_id_a]
    pB = papers_db[req.paper_id_b]
    return rag_engine.compare_papers(req.paper_id_a, req.paper_id_b, pA, pB)

@app.get("/api/export/{paper_id}")
async def export_paper_summary(paper_id: str, format: str = Query("markdown", enum=["markdown", "json"])):
    if paper_id not in papers_db:
        raise HTTPException(status_code=404, detail="Paper not found.")

    paper = papers_db[paper_id]
    summary = paper.get("summary", {})

    if format == "json":
        out_file = os.path.join(config.EXPORT_FOLDER, f"{paper_id}_summary.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        return FileResponse(out_file, filename=f"{paper['filename']}_summary.json", media_type="application/json")

    md_text = f"# {summary.get('title', paper['title'])}\n\n"
    md_text += f"**Authors:** {summary.get('authors', 'Unknown')}\n"
    md_text += f"**Filename:** {paper['filename']}\n\n---\n\n"
    md_text += f"## 📌 Abstract\n{summary.get('abstract_summary', 'N/A')}\n\n"
    md_text += "## 🚀 Key Contributions\n"
    for item in summary.get("key_contributions", []):
        md_text += f"- {item}\n"

    md_text += f"\n## 🔬 Methodology\n{summary.get('methodology', 'N/A')}\n\n"
    md_text += f"## 📊 Results\n{summary.get('results', 'N/A')}\n\n"
    md_text += f"## ⚠️ Limitations\n{summary.get('limitations', 'N/A')}\n"

    out_file = os.path.join(config.EXPORT_FOLDER, f"{paper_id}_summary.md")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(md_text)

    return FileResponse(out_file, filename=f"{paper['filename']}_summary.md", media_type="text/markdown")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
