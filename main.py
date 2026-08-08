import argparse
import os
import json
import sys

import config
from pdf_parser import parse_paper
from vector_store import VectorStore
from rag_engine import RAGEngine

def main():
    parser = argparse.ArgumentParser(description="Academic Paper Summariser CLI")
    parser.add_argument("pdf_path", type=str, help="Path to academic PDF paper")
    parser.add_argument("--query", type=str, help="Question to ask paper context", default=None)
    parser.add_argument("--export", choices=["json", "markdown"], help="Export format", default="markdown")
    parser.add_argument("--out", type=str, help="Output file path", default=None)

    args = parser.parse_args()

    if not os.path.exists(args.pdf_path):
        print(f"[ERROR] File '{args.pdf_path}' not found.")
        sys.exit(1)

    print(f"[INFO] Processing paper: {args.pdf_path}...")
    parsed = parse_paper(args.pdf_path, chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP)
    print(f"[OK] Extracted {parsed['total_pages']} pages into {parsed['total_chunks']} section-aware chunks.")

    # Initialize RAG Engine
    vector_store = VectorStore()
    vector_store.add_chunks(parsed["chunks"])
    rag = RAGEngine(vector_store)

    paper_info = {
        "paper_id": parsed["paper_id"],
        "title": parsed["title"],
        "filename": parsed["filename"]
    }

    print("\n[INFO] Generating structured paper summary...")
    result = rag.summarize_paper(parsed["paper_id"], paper_info)
    summary = result["summary"]

    print("\n" + "="*60)
    print(f"TITLE: {summary.get('title', parsed['title'])}")
    print("="*60)
    print(f"\nABSTRACT SUMMARY:\n{summary.get('abstract_summary')}\n")
    print("KEY CONTRIBUTIONS:")
    for item in summary.get("key_contributions", []):
        print(f"  * {item}")
    print(f"\nMETHODOLOGY:\n{summary.get('methodology')}\n")
    print(f"RESULTS:\n{summary.get('results')}\n")
    print(f"LIMITATIONS:\n{summary.get('limitations')}\n")

    if args.query:
        print(f"\n[QUERY]: '{args.query}'...")
        qa_res = rag.answer_question(args.query, paper_id=parsed["paper_id"])
        print("\nANSWER:")
        print(qa_res["answer"])

    # Export handling
    if args.out or args.export:
        out_file = args.out or f"summary.{'md' if args.export == 'markdown' else 'json'}"
        if args.export == "json":
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)
        else:
            md_text = f"# {summary.get('title')}\n\n## Abstract\n{summary.get('abstract_summary')}\n\n## Key Contributions\n"
            md_text += "\n".join([f"- {c}" for c in summary.get("key_contributions", [])])
            md_text += f"\n\n## Methodology\n{summary.get('methodology')}\n\n## Results\n{summary.get('results')}"
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(md_text)
        print(f"\n[EXPORT] Summary exported to: {out_file}")

if __name__ == "__main__":
    main()
