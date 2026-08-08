import re
import os
import uuid

SECTION_HEADERS = [
    (r'(?i)^\s*(?:1\.?\s*)?abstract\b', 'Abstract'),
    (r'(?i)^\s*(?:1\.?\s*|I\.?\s*)?introduction\b', 'Introduction'),
    (r'(?i)^\s*(?:2\.?\s*|II\.?\s*)?(?:related work|background)\b', 'Related Work'),
    (r'(?i)^\s*(?:3\.?\s*|III\.?\s*)?(?:methodology|method|methods|proposed approach|system model|architecture)\b', 'Methodology'),
    (r'(?i)^\s*(?:4\.?\s*|IV\.?\s*)?(?:experiments|experimental setup|results|evaluations)\b', 'Results'),
    (r'(?i)^\s*(?:5\.?\s*|V\.?\s*)?(?:discussion|analysis)\b', 'Discussion'),
    (r'(?i)^\s*(?:6\.?\s*|VI\.?\s*)?(?:conclusion|conclusions|future work)\b', 'Conclusion'),
    (r'(?i)^\s*(?:7\.?\s*|VII\.?\s*)?(?:references|bibliography)\b', 'References'),
]

def extract_pdf_pages(pdf_path):
    pages = []
    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            pages.append({"page": i + 1, "text": text.strip()})
    except Exception:
        try:
            import fitz
            doc = fitz.open(pdf_path)
            for i, page in enumerate(doc):
                pages.append({"page": i + 1, "text": page.get_text().strip()})
            doc.close()
        except Exception:
            with open(pdf_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            pages.append({"page": 1, "text": text.strip()})
    return pages

def detect_section(line):
    line = line.strip()
    if len(line) > 75:
        return None
    for pattern, section_name in SECTION_HEADERS:
        if re.search(pattern, line):
            return section_name
    return None

def parse_paper(pdf_path, chunk_size=800, chunk_overlap=150):
    filename = os.path.basename(pdf_path)
    paper_id = str(uuid.uuid4())[:8]
    pages = extract_pdf_pages(pdf_path)

    full_text = "\n\n".join([p["text"] for p in pages if p["text"]])

    lines = [l.strip() for l in full_text.split('\n') if l.strip()]
    title = lines[0] if lines else filename.replace('.pdf', '')
    if len(title) > 120:
        title = title[:120] + "..."

    chunks = []
    curr_section = "General"
    curr_text = ""
    curr_pages = set()
    chunk_count = 0

    for p in pages:
        page_num = p["page"]
        page_lines = p["text"].split('\n')

        for line in page_lines:
            header = detect_section(line)
            if header:
                curr_section = header

            curr_text += line + "\n"
            curr_pages.add(page_num)

            if len(curr_text) >= chunk_size:
                text_block = curr_text.strip()
                if text_block:
                    chunks.append({
                        "paper_id": paper_id,
                        "paper_title": title,
                        "filename": filename,
                        "chunk_id": f"{paper_id}_c{chunk_count}",
                        "chunk_index": chunk_count,
                        "section": curr_section,
                        "pages": sorted(list(curr_pages)),
                        "text": text_block,
                        "token_count": len(text_block.split())
                    })
                    chunk_count += 1

                curr_text = curr_text[-chunk_overlap:] if len(curr_text) > chunk_overlap else ""
                curr_pages = {page_num}

    if curr_text.strip():
        chunks.append({
            "paper_id": paper_id,
            "paper_title": title,
            "filename": filename,
            "chunk_id": f"{paper_id}_c{chunk_count}",
            "chunk_index": chunk_count,
            "section": curr_section,
            "pages": sorted(list(curr_pages)),
            "text": curr_text.strip(),
            "token_count": len(curr_text.strip().split())
        })

    return {
        "paper_id": paper_id,
        "title": title,
        "filename": filename,
        "total_pages": len(pages),
        "total_chunks": len(chunks),
        "full_text": full_text,
        "chunks": chunks
    }
