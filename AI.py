

import os
import pdfplumber
from docx import Document
from pptx import Presentation
from groq import Groq
from langchain_text_splitters import RecursiveCharacterTextSplitter


# ================= TEXT EXTRACTION =================

def extract_text(file_path: str) -> str:
    file_path = file_path.strip().strip('"').strip("'")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    file_type = file_path.split(".")[-1].lower()

    if file_type == "pdf":
        return extract_pdf_text(file_path)
    elif file_type == "docx":
        return extract_docx_text(file_path)
    elif file_type == "pptx":
        return extract_pptx_text(file_path)
    elif file_type == "txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file format: .{file_type}")


def extract_pdf_text(file_path: str) -> str:
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()


def extract_docx_text(file_path: str) -> str:
    doc = Document(file_path)
    return "\n".join(p.text for p in doc.paragraphs).strip()


def extract_pptx_text(file_path: str) -> str:
    prs = Presentation(file_path)
    text = ""
    for slide in prs.slides:
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                text += shape.text + "\n"
    return text.strip()


# ================= GROQ SETUP =================



GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = (
    "You are an expert document analysis and summarization AI. "
    "You produce accurate, coherent, and high-quality summaries."
)

splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=200
)


# ================= PREPROCESSING (LLM POWER) =================

def preprocess_text_with_llm(raw_text: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert document preprocessing AI. "
                    "Your task is to clean and normalize extracted document text."
                )
            },
            {
                "role": "user",
                "content": f"""
INSTRUCTIONS:
- Remove headers, footers, page numbers
- Remove duplicated or repeated content
- Fix broken sentences and paragraphs
- Convert bullet points into complete sentences
- Remove formatting noise and symbols
- Preserve all important information
- Maintain logical flow
- DO NOT summarize

TEXT:
{raw_text}
"""
            }
        ],
        temperature=0.2,
        max_tokens=3000
    )

    return response.choices[0].message.content.strip()


# ================= CORE SUMMARIZATION =================

def _summarize(text: str, final_prompt: str) -> str:
    if not text.strip():
        raise ValueError("Text cannot be empty")

    # 1️⃣ PREPROCESS FULL DOCUMENT
    cleaned_text = preprocess_text_with_llm(text)

    # 2️⃣ SPLIT CLEAN TEXT
    chunks = splitter.split_text(cleaned_text)
    chunk_summaries = []

    # 3️⃣ CHUNK-LEVEL SUMMARIES
    for chunk in chunks:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"""
Summarize this section clearly and accurately.
Focus only on meaningful ideas and key points.

TEXT:
{chunk}
"""
                }
            ],
            temperature=0.3,
            max_tokens=700
        )

        chunk_summaries.append(
            response.choices[0].message.content.strip()
        )

    # 4️⃣ FINAL GLOBAL SUMMARY
    combined_summary = "\n\n".join(chunk_summaries)

    final_response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"""
{final_prompt}

DOCUMENT CONTENT:
{combined_summary}
"""
            }
        ],
        temperature=0.3,
        max_tokens=1200
    )

    return final_response.choices[0].message.content.strip()


# ================= SUMMARY TYPES =================

def short_summary(text: str) -> str:
    prompt = """
Create an executive-level summary using 7–10 concise bullet points.
Focus on core ideas, insights, and conclusions.
Avoid repetition and fluff.
"""
    return _summarize(text, prompt)


def medium_summary(text: str) -> str:
    prompt = """
Write a professional and coherent summary of 180–250 words.
Maintain logical flow.
Cover all major concepts, arguments, and conclusions.
"""
    return _summarize(text, prompt)


def long_summary(text: str) -> str:
    prompt = """
Create a detailed, structured summary with clear headings:
- Introduction
- Main Sections
- Key Findings / Arguments
- Conclusion

Explain ideas clearly and comprehensively.
Avoid redundancy.
"""
    return _summarize(text, prompt)
