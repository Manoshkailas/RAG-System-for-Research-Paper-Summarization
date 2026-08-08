import os
import json
import streamlit as st
import config
from pdf_parser import parse_paper
from vector_store import VectorStore
from rag_engine import RAGEngine

# Page configuration
st.set_page_config(
    page_title="Academic Paper Summariser",
    page_icon="📄",
    layout="wide"
)

# Initialize vector store and RAG engine in session state
if "vector_store" not in st.session_state:
    st.session_state.vector_store = VectorStore()
if "rag_engine" not in st.session_state:
    st.session_state.rag_engine = RAGEngine(st.session_state.vector_store)
if "papers_db" not in st.session_state:
    st.session_state.papers_db = {}
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Header
st.title("📄 Academic Paper Summariser (LLM + RAG)")
st.write("Upload PDF research papers to extract structured summaries, ask questions, and compare papers.")

# Sidebar for PDF upload
st.sidebar.header("Upload Papers")
uploaded_files = st.sidebar.file_uploader("Choose PDF paper(s)", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    for f in uploaded_files:
        if f.name not in [p["filename"] for p in st.session_state.papers_db.values()]:
            file_path = os.path.join(config.UPLOAD_FOLDER, f.name)
            with open(file_path, "wb") as out:
                out.write(f.getbuffer())

            with st.spinner(f"Ingesting {f.name}..."):
                parsed = parse_paper(file_path)
                pid = parsed["paper_id"]
                st.session_state.vector_store.add_chunks(parsed["chunks"])

                paper_entry = {
                    "paper_id": pid,
                    "title": parsed["title"],
                    "filename": parsed["filename"],
                    "total_pages": parsed["total_pages"],
                    "total_chunks": parsed["total_chunks"],
                    "parsed_data": parsed
                }

                # Generate summary on load
                res = st.session_state.rag_engine.summarize_paper(pid, paper_entry)
                paper_entry["summary"] = res["summary"]
                paper_entry["retrieved_chunks"] = res["retrieved_chunks"]

                st.session_state.papers_db[pid] = paper_entry
                st.sidebar.success(f"Loaded: {f.name}")

# App Navigation Tabs
tab_summary, tab_qa, tab_compare, tab_chunks = st.tabs([
    "Structured Summary", "Interactive Q&A", "Paper Comparison", "Chunk Inspector"
])

# Tab 1: Summary
with tab_summary:
    if not st.session_state.papers_db:
        st.info("Upload a PDF paper in the sidebar to view its summary.")
    else:
        paper_map = {p["title"]: pid for pid, p in st.session_state.papers_db.items()}
        selected_title = st.selectbox("Select Paper:", list(paper_map.keys()))
        selected_pid = paper_map[selected_title]
        paper = st.session_state.papers_db[selected_pid]
        s = paper.get("summary", {})

        st.subheader(s.get("title", paper["title"]))
        st.caption(f"Authors: {s.get('authors', 'Unknown')} | Pages: {paper['total_pages']} | Chunks: {paper['total_chunks']}")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### Abstract Summary")
            st.write(s.get("abstract_summary", "N/A"))

        with c2:
            st.markdown("### Key Contributions")
            for item in s.get("key_contributions", []):
                st.markdown(f"- {item}")

        col_m, col_r, col_l = st.columns(3)
        with col_m:
            st.markdown("### Methodology")
            st.write(s.get("methodology", "N/A"))
        with col_r:
            st.markdown("### Results")
            st.write(s.get("results", "N/A"))
        with col_l:
            st.markdown("### Limitations")
            st.write(s.get("limitations", "N/A"))

        # Export button
        md_text = f"# {s.get('title')}\n\n## Abstract\n{s.get('abstract_summary')}\n\n## Key Contributions\n"
        md_text += "\n".join([f"- {c}" for c in s.get("key_contributions", [])])
        st.download_button("Download Summary (Markdown)", data=md_text, file_name=f"{paper['filename']}_summary.md", mime="text/markdown")

# Tab 2: Q&A
with tab_qa:
    st.subheader("Ask a Question About the Paper")
    if not st.session_state.papers_db:
        st.info("Upload a paper in the sidebar to start asking questions.")
    else:
        paper_options = {"All Loaded Papers": None}
        for p_id, p_info in st.session_state.papers_db.items():
            paper_options[p_info["title"]] = p_id

        selected_qa_paper = st.selectbox("Select Target Paper:", list(paper_options.keys()))
        selected_qa_pid = paper_options[selected_qa_paper]

        user_q = st.text_input("Question:", placeholder="What datasets or methods were used?")
        if st.button("Ask") and user_q:
            res = st.session_state.rag_engine.answer_question(user_q, paper_id=selected_qa_pid)
            st.session_state.chat_history.append({"user": user_q, "bot": res["answer"], "chunks": res["retrieved_chunks"]})

        for chat in reversed(st.session_state.chat_history):
            with st.chat_message("user"):
                st.write(chat["user"])
            with st.chat_message("assistant"):
                st.write(chat["bot"])
                if chat["chunks"]:
                    with st.expander("Retrieved Context Chunks"):
                        for chunk in chat["chunks"]:
                            st.caption(f"Section: {chunk['section']} | Page {chunk['pages']}")
                            st.code(chunk["text"][:250] + "...")

# Tab 3: Comparison
with tab_compare:
    st.subheader("Compare Two Papers")
    if len(st.session_state.papers_db) < 2:
        st.warning("Upload at least 2 papers to enable comparison mode.")
    else:
        keys = list(st.session_state.papers_db.keys())
        pid_a = st.selectbox("Paper A", keys, format_func=lambda x: st.session_state.papers_db[x]["title"])
        pid_b = st.selectbox("Paper B", keys, format_func=lambda x: st.session_state.papers_db[x]["title"])

        if st.button("Compare"):
            pA = st.session_state.papers_db[pid_a]
            pB = st.session_state.papers_db[pid_b]
            comp = st.session_state.rag_engine.compare_papers(pid_a, pid_b, pA, pB)["comparison"]

            c_left, c_right = st.columns(2)
            with c_left:
                st.markdown("#### Problem Comparison")
                st.write(comp.get("core_problem_comparison"))
                st.markdown("#### Methodology Contrast")
                st.write(comp.get("methodology_comparison"))

            with c_right:
                st.markdown("#### Results & Performance")
                st.write(comp.get("results_comparison"))
                st.markdown("#### Recommendation")
                st.write(comp.get("recommendation"))

# Tab 4: Chunk Inspector
with tab_chunks:
    st.subheader("Chunk & Citation Inspector")
    if not st.session_state.papers_db:
        st.info("No papers loaded yet.")
    else:
        pid = st.selectbox("Inspect Paper:", list(st.session_state.papers_db.keys()), format_func=lambda x: st.session_state.papers_db[x]["title"])
        paper = st.session_state.papers_db[pid]
        for i, chunk in enumerate(paper.get("retrieved_chunks", [])):
            st.markdown(f"**Chunk #{i+1} | Section: `{chunk.get('section')}` | Page: `{chunk.get('pages')}`**")
            st.text_area("Content", value=chunk.get("snippet", chunk.get("text", "")), height=90, key=f"inspect_{i}")
