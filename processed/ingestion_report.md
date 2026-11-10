# Enterprise Policy Dataset Ingestion & Preparation Report

**Date**: 2026-11-08 21:34:51  
**Knowledge Source**: 150 Editable DOCX Policies across 10 Departments  
**Vector Database**: Persistent Chroma DB (`vectorstore/chroma_db`)  
**Embedding Service**: BAAI/bge-m3 (1024 dimensions)  
**Execution Time**: 92.23 seconds  

---

## 1. Ingestion Summary

| Metric | Value |
|---|---|
| **Total Expected Policies** | 150 |
| **Successful Documents** | 150 / 150 |
| **Failed Documents** | 0 |
| **Total Numbered Sections Extracted** | 1950 |
| **Total Child Chunks Generated** | 2100 |
| **Total Chunks in Chroma Database** | 2100 |
| **Duplicate Indexing Prevention** | Enforced (idempotent upsert & ID existence check) |

---

## 2. Department Breakdown (10 Departments Represented)

| Code | Department Name | Policies Processed | Chunks Generated | Ingestion Status |
|---|---|---|---|---|
| HR | Human Resources | 15 | 210 | Completed |
| IT | Information Technology | 15 | 210 | Completed |
| FIN | Finance | 15 | 210 | Completed |
| LEG | Legal & Compliance | 15 | 210 | Completed |
| OPS | Operations | 15 | 210 | Completed |
| SEC | Security | 15 | 210 | Completed |
| PROC | Procurement | 15 | 210 | Completed |
| SALES | Sales | 15 | 210 | Completed |
| MKT | Marketing | 15 | 210 | Completed |
| GOV | Governance, Risk & Assurance | 15 | 210 | Completed |

---

## 3. Storage & Artifact Hierarchy

- **Primary Clean DOCX Repository**: `policies/<Department>/` (150 DOCX files only)
- **Canonical Master Metadata**: `metadata/Policy_Register.csv`
- **Extracted Structured Documents**: `processed/extracted_policies.json`
- **Searchable Child Chunks**: `processed/chunks.json` (300–500 tokens, 50–80 overlap)
- **Parent Sections Map**: `processed/parent_sections.json`
- **Persistent Vector DB**: `vectorstore/chroma_db/`
