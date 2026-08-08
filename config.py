import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))
TOP_K_RESULTS = int(os.getenv("TOP_K_RESULTS", "4"))

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
EXPORT_FOLDER = os.path.join(os.path.dirname(__file__), "exports")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXPORT_FOLDER, exist_ok=True)

SUMMARY_PROMPT = """
You are an expert research assistant. Read the provided academic paper excerpts and create a structured summary.

Return your response strictly in valid JSON format:
{
  "title": "Paper Title",
  "authors": "Authors list or Unknown",
  "abstract_summary": "2-3 sentence summary of the paper problem and solution",
  "key_contributions": [
    "Contribution 1",
    "Contribution 2",
    "Contribution 3"
  ],
  "methodology": "Explanation of the approach, algorithms, or architecture used",
  "results": "Main experimental results, benchmarks, and performance metrics",
  "limitations": "Limitations, constraints, or future directions mentioned"
}
"""

QA_PROMPT = """
Answer the user's question accurately based ONLY on the provided research paper chunks.
If the answer isn't in the chunks, say so clearly. Mention relevant section names if helpful.
"""

COMPARISON_PROMPT = """
Compare these two research papers based on their excerpts.
Return a JSON object:
{
  "paper_a_title": "Title of Paper A",
  "paper_b_title": "Title of Paper B",
  "core_problem_comparison": "How their target problems differ or overlap",
  "methodology_comparison": "Comparison of their techniques and architectures",
  "results_comparison": "Comparison of their performance and benchmarks",
  "pros_cons": {
    "paper_a_strengths": ["Strength 1", "Strength 2"],
    "paper_b_strengths": ["Strength 1", "Strength 2"]
  },
  "recommendation": "When to choose Paper A vs Paper B"
}
"""
