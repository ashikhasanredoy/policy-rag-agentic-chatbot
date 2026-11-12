#!/usr/bin/env python3
"""
Markdown Ingestion & Chroma Vector Indexing Pipeline.
Ingests all 150 Markdown policy files from policies/<DEPT>/*.md into ChromaDB and BM25.
Strictly ignores DOCX and PDF files.
"""

import os
import sys
import re
import csv
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import chromadb
from src.embeddings.embedding_model import embedding_service

POLICIES_DIR = PROJECT_ROOT / "policies"
METADATA_CSV = PROJECT_ROOT / "metadata" / "Policy_Register.csv"
PROCESSED_DIR = PROJECT_ROOT / "processed"
VECTORSTORE_DIR = PROJECT_ROOT / "vectorstore" / "chroma_db"

DEPT_NAMES = {
    "HR": "Human Resources",
    "IT": "Information Technology",
    "FIN": "Finance",
    "LEG": "Legal & Compliance",
    "OPS": "Operations",
    "SEC": "Security",
    "PROC": "Procurement",
    "SALES": "Sales",
    "MKT": "Marketing",
    "GOV": "Governance, Risk & Assurance",
}


def load_metadata_register() -> Dict[str, Dict[str, Any]]:
    register = {}
    with open(METADATA_CSV, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            pid = r["Policy ID"].strip()
            register[pid] = r
    return register


def parse_markdown_policy(md_path: Path, register: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    content = md_path.read_text(encoding="utf-8")

    # Policy ID
    m_id = re.search(r"([A-Z]{2,5}-\d{3})", md_path.name)
    pid = m_id.group(1) if m_id else ""
    dept_code = md_path.parent.name

    meta = register.get(pid, {})
    title = meta.get("Policy Title", md_path.stem.replace(f"{pid}_", "").replace("_", " "))
    dept = meta.get("Department", DEPT_NAMES.get(dept_code, dept_code))
    version = meta.get("Version", "1.0")
    effective_date = meta.get("Effective Date", "2026-11-08")
    review_date = meta.get("Next Review", "2027-11-08")
    status = meta.get("Status", "Approved baseline")

    # Extract sections: ## <num>. <title>
    sec_pattern = re.compile(r"^##\s+(\d{1,2})\.\s+(.+)$", re.MULTILINE)
    sections = []
    matches = list(sec_pattern.finditer(content))

    for i, m in enumerate(matches):
        sec_num = m.group(1)
        sec_title = m.group(2).strip()
        start_pos = m.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        sec_text = content[start_pos:end_pos].strip()

        sections.append({
            "section_number": sec_num,
            "section_title": sec_title,
            "text": sec_text
        })

    rel_source_file = f"policies/{dept_code}/{md_path.name}"

    return {
        "policy_id": pid,
        "policy_title": title,
        "department": dept,
        "department_code": dept_code,
        "version": version,
        "effective_date": effective_date,
        "review_date": review_date,
        "status": status,
        "classification": "Internal",
        "source_file": rel_source_file,
        "file_type": "MD",
        "section_count": len(sections),
        "sections": sections
    }


def chunk_policy_document(doc_data: Dict[str, Any], target_tokens: int = 400, overlap_tokens: int = 60) -> Tuple[List[Dict[str, Any]], Dict[str, str]]:
    chunks = []
    parent_sections = {}

    pid = doc_data["policy_id"]
    title = doc_data["policy_title"]
    dept = doc_data["department"]
    dept_code = doc_data["department_code"]
    version = doc_data["version"]
    effective_date = doc_data["effective_date"]
    review_date = doc_data["review_date"]
    status = doc_data["status"]
    source_file = doc_data["source_file"]

    chunk_counter = 1

    for sec in doc_data["sections"]:
        sec_num = sec["section_number"]
        sec_title = sec["section_title"]
        sec_text = sec["text"]

        parent_id = f"{pid}-SEC-{sec_num.zfill(2)}"
        parent_sections[parent_id] = f"## {pid} — {title}\n### Section {sec_num}: {sec_title}\n{sec_text}"

        token_est = int(len(sec_text.split()) * 1.3)

        if token_est <= target_tokens + overlap_tokens:
            header = f"[{pid}: {title} | Department: {dept} | Section {sec_num}: {sec_title}]"
            chunk_text = f"{header}\n{sec_text}"
            cid = f"{pid}-CHUNK-{chunk_counter:03d}"
            chunks.append({
                "chunk_id": cid,
                "parent_id": parent_id,
                "text": chunk_text,
                "metadata": {
                    "policy_id": pid,
                    "policy_title": title,
                    "department": dept,
                    "department_code": dept_code,
                    "section_number": sec_num,
                    "section_title": sec_title,
                    "version": version,
                    "effective_date": effective_date,
                    "review_date": review_date,
                    "status": status,
                    "parent_id": parent_id,
                    "chunk_id": cid,
                    "source_file": source_file,
                    "file_type": "MD",
                    "token_count": int(len(chunk_text.split()) * 1.3)
                }
            })
            chunk_counter += 1
        else:
            paragraphs = [p.strip() for p in sec_text.split("\n\n") if p.strip()]
            current_words: List[str] = []

            for p in paragraphs:
                p_words = p.split()
                if not p_words:
                    continue

                if len(current_words) + len(p_words) <= int(target_tokens / 1.3):
                    current_words.extend(p_words)
                else:
                    if current_words:
                        sub_text = " ".join(current_words)
                        header = f"[{pid}: {title} | Department: {dept} | Section {sec_num}: {sec_title}]"
                        chunk_text = f"{header}\n{sub_text}"
                        cid = f"{pid}-CHUNK-{chunk_counter:03d}"
                        chunks.append({
                            "chunk_id": cid,
                            "parent_id": parent_id,
                            "text": chunk_text,
                            "metadata": {
                                "policy_id": pid,
                                "policy_title": title,
                                "department": dept,
                                "department_code": dept_code,
                                "section_number": sec_num,
                                "section_title": sec_title,
                                "version": version,
                                "effective_date": effective_date,
                                "review_date": review_date,
                                "status": status,
                                "parent_id": parent_id,
                                "chunk_id": cid,
                                "source_file": source_file,
                                "file_type": "MD",
                                "token_count": int(len(chunk_text.split()) * 1.3)
                            }
                        })
                        chunk_counter += 1

                        overlap_word_count = int(overlap_tokens / 1.3)
                        current_words = current_words[-overlap_word_count:] + p_words
                    else:
                        current_words = p_words

            if current_words:
                sub_text = " ".join(current_words)
                header = f"[{pid}: {title} | Department: {dept} | Section {sec_num}: {sec_title}]"
                chunk_text = f"{header}\n{sub_text}"
                cid = f"{pid}-CHUNK-{chunk_counter:03d}"
                chunks.append({
                    "chunk_id": cid,
                    "parent_id": parent_id,
                    "text": chunk_text,
                    "metadata": {
                        "policy_id": pid,
                        "policy_title": title,
                        "department": dept,
                        "department_code": dept_code,
                        "section_number": sec_num,
                        "section_title": sec_title,
                        "version": version,
                        "effective_date": effective_date,
                        "review_date": review_date,
                        "status": status,
                        "parent_id": parent_id,
                        "chunk_id": cid,
                        "source_file": source_file,
                        "file_type": "MD",
                        "token_count": int(len(chunk_text.split()) * 1.3)
                    }
                })
                chunk_counter += 1

    return chunks, parent_sections


def main():
    print("=" * 80)
    print("INGESTING 150 MARKDOWN POLICIES INTO CHROMA VECTOR DATABASE")
    print("=" * 80)

    register = load_metadata_register()
    all_extracted = []
    all_chunks = []
    all_parents = {}

    md_files = sorted(list(POLICIES_DIR.rglob("*.md")))
    print(f"Discovered {len(md_files)} Markdown policies across department folders in policies/.")

    if len(md_files) != 150:
        raise ValueError(f"Expected 150 Markdown files, found {len(md_files)}")

    for md_path in md_files:
        doc_data = parse_markdown_policy(md_path, register)
        all_extracted.append(doc_data)

        chunks, parents = chunk_policy_document(doc_data)
        all_chunks.extend(chunks)
        all_parents.update(parents)

    print(f"[✓] Parsed {len(all_extracted)} Markdown documents into {len(all_chunks)} chunks and {len(all_parents)} parent sections.")

    # Save to processed/
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROCESSED_DIR / "extracted_policies.json", "w", encoding="utf-8") as f:
        json.dump(all_extracted, f, indent=2, ensure_ascii=False)
    with open(PROCESSED_DIR / "chunks.json", "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    with open(PROCESSED_DIR / "parent_sections.json", "w", encoding="utf-8") as f:
        json.dump(all_parents, f, indent=2, ensure_ascii=False)
    print("[✓] Saved extracted JSON artifacts to processed/.")

    # Rebuild Chroma collection
    print(f"\nConnecting to Chroma persistent client at: {VECTORSTORE_DIR}")
    client = chromadb.PersistentClient(path=str(VECTORSTORE_DIR))
    try:
        client.delete_collection("enterprise_policies")
        print("[✓] Cleared previous collection to ensure zero duplicate chunks.")
    except Exception:
        pass

    collection = client.create_collection(
        name="enterprise_policies",
        metadata={"hnsw:space": "cosine"}
    )

    batch_size = 100
    total_chunks = len(all_chunks)
    print(f"Indexing {total_chunks} Markdown chunks using BGE-M3 embeddings...")

    start_t = time.perf_counter()
    for i in range(0, total_chunks, batch_size):
        batch = all_chunks[i:i + batch_size]
        b_ids = [c["chunk_id"] for c in batch]
        b_texts = [c["text"] for c in batch]
        b_metas = [c["metadata"] for c in batch]

        b_embeddings = embedding_service.embed_documents(b_texts)

        collection.upsert(
            ids=b_ids,
            embeddings=b_embeddings,
            documents=b_texts,
            metadatas=b_metas
        )
        print(f"  Indexed {min(i + batch_size, total_chunks)}/{total_chunks} chunks...")

    dur_s = time.perf_counter() - start_t
    print(f"[✓] Chroma vector indexing completed in {dur_s:.1f}s. Total chunks in DB: {collection.count()}")

    print("\n" + "=" * 80)
    print("MARKDOWN INGESTION & VECTOR DATABASE INDEXING COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    main()

