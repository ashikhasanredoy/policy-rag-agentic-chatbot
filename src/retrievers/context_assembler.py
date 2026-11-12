"""
Context Assembler for Enterprise Policy RAG.
Validates metadata, removes duplicates, prevents cross-policy contamination,
and organizes verified chunks with strict section provenance.
"""

from typing import List, Dict, Any, Tuple, Optional
from src.ingestion.metadata_extractor import metadata_registry


class ContextAssembler:
    """Assembles and verifies evidence chunks before LLM generation."""

    @staticmethod
    def validate_and_assemble_context(
        chunks: List[Dict[str, Any]],
        target_policy_id: Optional[str] = None,
        target_policies: Optional[List[str]] = None,
        max_chunks: int = 5
    ) -> Tuple[List[Dict[str, Any]], str, Dict[str, Any]]:
        """
        Validates metadata, purges cross-policy contaminants when a specific policy is targeted,
        deduplicates, and builds clean assembled context.
        """
        if not chunks:
            return [], "", {"valid": False, "reason": "No candidate chunks"}

        verified_chunks: List[Dict[str, Any]] = []
        seen_texts = set()
        seen_sections = set()
        rejected_count = 0

        # If target policies are explicitly identified, prioritize and isolate chunks belonging to them
        candidate_pool = chunks
        if target_policies:
            target_matches = [c for c in chunks if c.get("metadata", {}).get("policy_id") in target_policies]
            if target_matches:
                candidate_pool = target_matches
        elif target_policy_id:
            target_matches = [c for c in chunks if c.get("metadata", {}).get("policy_id") == target_policy_id]
            if target_matches:
                # If target policy has matches, isolate to that policy to prevent cross-contamination
                candidate_pool = target_matches

        for c in candidate_pool:
            meta = c.get("metadata", {})
            pid = meta.get("policy_id", "")
            title = meta.get("policy_title", "")
            sec_num = str(meta.get("section_number", ""))
            sec_title = meta.get("section_title", "")

            # 1. Verify Policy ID exists in Policy Register
            canonical_meta = metadata_registry.get_metadata(pid)
            if not canonical_meta:
                rejected_count += 1
                continue

            # 2. Verify Title matches or is consistent
            if canonical_meta.get("policy_title") and title:
                if canonical_meta["policy_title"].lower() != title.lower():
                    # Correct to canonical title
                    meta["policy_title"] = canonical_meta["policy_title"]

            # 3. Deduplicate exact or near-identical text
            text_body = c.get("compressed_text", c.get("text", "")).strip()
            # Strip header prefix if present
            if text_body.startswith("[") and "]\n" in text_body:
                text_body = text_body.split("]\n", 1)[-1].strip()

            text_signature = f"{pid}_{text_body[:100].lower()}"
            section_sig = f"{pid}-S{sec_num}"

            if text_signature in seen_texts:
                continue
            seen_texts.add(text_signature)

            # Preserve at most 2 chunks per section to keep diversity
            section_count = sum(1 for s in seen_sections if s == section_sig)
            if section_count >= 2:
                continue
            seen_sections.add(section_sig)

            # For multi-policy context, avoid letting a single policy monopolize all slots
            if not target_policy_id:
                policy_chunk_count = sum(1 for v in verified_chunks if v.get("metadata", {}).get("policy_id") == pid)
                if policy_chunk_count >= 2:
                    continue

            verified_chunks.append(c)
            # Allow up to 8 chunks when multiple policies are included for comparative/cross-policy synthesis
            effective_limit = max_chunks if (target_policy_id and not target_policies) else max(max_chunks, 8)
            if len(verified_chunks) >= effective_limit:
                break

        if not verified_chunks:
            return [], "", {"valid": False, "reason": "No chunks passed metadata validation"}

        # 4. Group by Policy ID and sort by section number
        def sort_key(chunk):
            m = chunk.get("metadata", {})
            s_num = m.get("section_number", "99")
            try:
                return (m.get("policy_id", ""), int(s_num))
            except ValueError:
                return (m.get("policy_id", ""), 99)

        verified_chunks.sort(key=sort_key)

        # 5. Format assembled context string with clear boundaries matching Phase 11 specification
        context_blocks = []
        for idx, c in enumerate(verified_chunks, start=1):
            m = c.get("metadata", {})
            pid = m.get("policy_id", "")
            p_title = m.get("policy_title", "")
            dept = m.get("department", "")
            sec_num = m.get("section_number", "")
            sec_title = m.get("section_title", "")
            cid = c.get("chunk_id", f"{pid}-CHUNK-{idx:03d}")
            src_file = m.get("source_file", f"{pid}.md")

            text_content = c.get("compressed_text", c.get("text", "")).strip()
            if text_content.startswith("[") and "]\n" in text_content:
                text_content = text_content.split("]\n", 1)[-1].strip()

            block = (
                f"POLICY ID: {pid}\n"
                f"POLICY TITLE: {p_title}\n"
                f"DEPARTMENT: {dept}\n"
                f"SOURCE FILE: {src_file}\n"
                f"SECTION NUMBER: {sec_num}\n"
                f"SECTION TITLE: {sec_title}\n"
                f"CHUNK ID: {cid}\n"
                f"SOURCE TEXT:\n"
                f"{text_content}\n\n"
                f"END POLICY EVIDENCE."
            )
            context_blocks.append(block)

        assembled_context_str = "\n\n".join(context_blocks)
        validation_info = {
            "valid": True,
            "verified_chunks_count": len(verified_chunks),
            "rejected_chunks_count": rejected_count,
            "target_policy_isolated": bool(target_policy_id and len(verified_chunks) > 0 and all(c.get("metadata", {}).get("policy_id") == target_policy_id for c in verified_chunks))
        }

        return verified_chunks, assembled_context_str, validation_info


context_assembler = ContextAssembler()

