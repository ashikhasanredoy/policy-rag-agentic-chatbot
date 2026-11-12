"""
Idempotent Master Ingestion Pipeline for 150 Enterprise Policies.
Extracts structured sections from DOCX (PDF fallback), chunks into Parent-Child
hierarchy, generates embeddings, builds persistent Chroma vector store and BM25 index.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple
from src.config.settings import settings
from src.ingestion.document_loader import unified_loader
from src.ingestion.chunking import policy_chunker, PolicyChunk
from src.retrievers.vector_retriever import chroma_retriever
from src.retrievers.bm25_retriever import bm25_retriever
from src.retrievers.parent_retriever import parent_retriever


class EnterprisePolicyIndexer:
    """Orchestrates indexing of the 150-policy dataset into persistent storage."""

    def __init__(self, policies_dir: Path = settings.POLICIES_DIR):
        self.policies_dir = policies_dir
        self.manifest_file = settings.PROCESSED_DATA_DIR / "index_manifest.json"

    def compute_file_hash(self, file_path: Path) -> str:
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    def discover_policy_files(self) -> List[Path]:
        """Discovers primary policy files (DOCX preferred, PDF fallback)."""
        docx_files = list(self.policies_dir.glob("*/*.docx"))
        if docx_files:
            return sorted(docx_files)

        # Fallback to PDFs if no docx found
        pdf_files = list(self.policies_dir.glob("*/*.pdf"))
        return sorted(pdf_files)

    def run_indexing(self, force_reindex: bool = False) -> Dict[str, Any]:
        """Indexes all discovered policy documents idempotently."""
        files = self.discover_policy_files()
        print(f"📦 Discovered {len(files)} policy documents in {self.policies_dir.name}")

        # Load previous manifest for idempotency
        old_manifest = {}
        if not force_reindex and self.manifest_file.exists():
            try:
                with open(self.manifest_file, "r", encoding="utf-8") as f:
                    old_manifest = json.load(f)
            except Exception:
                pass

        all_chunks: List[PolicyChunk] = []
        new_manifest = {}
        processed_count = 0
        skipped_count = 0

        for idx, file_path in enumerate(files, 1):
            f_hash = self.compute_file_hash(file_path)
            new_manifest[str(file_path)] = f_hash

            # Idempotency check
            if not force_reindex and old_manifest.get(str(file_path)) == f_hash and chroma_retriever.count() > 0:
                skipped_count += 1
                continue

            try:
                parsed = unified_loader.load_policy(file_path)
                chunks, parent_dict = policy_chunker.chunk_policy(parsed)
                all_chunks.extend(chunks)
                parent_retriever.add_parent_sections(parent_dict)
                processed_count += 1

                if idx % 25 == 0 or idx == len(files):
                    print(f"[{idx}/{len(files)}] Processed {file_path.stem} -> {len(chunks)} chunks")

            except Exception as e:
                print(f"❌ Error processing {file_path.name}: {e}")

        # If re-indexing or new documents processed, update indexes
        if all_chunks:
            print(f"🚀 Updating vector index with {len(all_chunks)} new/updated chunks...")
            chroma_retriever.add_chunks(all_chunks)
            bm25_retriever.index_chunks(all_chunks)
            parent_retriever.save()

            # Save updated manifest
            with open(self.manifest_file, "w", encoding="utf-8") as f:
                json.dump(new_manifest, f, indent=2)
            print("✅ Indexing complete and manifest updated.")
        elif skipped_count > 0:
            print(f"⚡ Idempotent check: All {skipped_count} policy files are already up-to-date in index.")
            # Ensure in-memory BM25 and parent retriever are loaded
            if not bm25_retriever.corpus:
                self._load_corpus_from_store()

        return {
            "total_files": len(files),
            "processed": processed_count,
            "skipped": skipped_count,
            "vector_count": chroma_retriever.count(),
            "parent_sections_count": len(parent_retriever.parent_store)
        }

    def _load_corpus_from_store(self):
        """Loads chunks from vector store into BM25 if already indexed."""
        results = chroma_retriever.collection.get(include=["documents", "metadatas"])
        if results and results.get("ids"):
            chunks = []
            for cid, doc, meta in zip(results["ids"], results["documents"], results["metadatas"]):
                chunks.append(PolicyChunk(chunk_id=cid, parent_id=meta.get("parent_id", ""), text=doc, metadata=meta))
            bm25_retriever.index_chunks(chunks)


indexer = EnterprisePolicyIndexer()

