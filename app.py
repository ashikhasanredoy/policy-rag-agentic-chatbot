#!/usr/bin/env python3
"""
Enterprise Policy RAG System - Main Application Interface.
Supports interactive REPL, single-query CLI execution, dataset indexing, benchmark evaluation,
and complete Retrieval Debugging Mode.

Usage:
    python app.py                     # Launch interactive Q&A REPL
    python app.py -q "What is HR-003?" # Run single query
    python app.py -q "What is the procedure for employee expense reimbursement?" --debug
    python app.py --index             # Re-index all 150 enterprise policy documents
    python app.py --eval              # Run 7-architecture evaluation benchmark
    python app.py --api               # Launch FastAPI REST API server
"""

import sys
import time
import json
import argparse
from typing import Optional
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.workflow.graph import run_policy_rag
from src.retrievers.multi_query import query_expander


def print_banner():
    banner = r"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                   ENTERPRISE POLICY HYBRID RAG SYSTEM                         ║
║               150 Policies | 10 Departments | English & Bangla                ║
║           Dense (BGE-M3) + Lexical (BM25) + RRF + Cross-Encoder Rerank         ║
║                    Strict Zero-Hallucination & Evidence Verified              ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def display_debug_trace(debug_trace: dict):
    """Displays the comprehensive 11-point Retrieval Debugging Trace."""
    print("\n" + "🔍" * 40)
    print("                     RETRIEVAL DEBUGGING MODE TRACE")
    print("🔍" * 40)

    print(f"\n[1. Original User Question]\n  {debug_trace.get('1. Original User Question', 'N/A')}")
    print(f"\n[2. Detected Department]\n  {debug_trace.get('2. Detected Department', 'N/A')}")
    print(f"\n[3. Detected Policy ID]\n  {debug_trace.get('3. Detected Policy ID', 'N/A')}")

    print("\n[4. BM25 Search Results (Top Lexical Hits)]")
    bm25_hits = debug_trace.get("4. BM25 Results", [])
    if bm25_hits:
        for idx, h in enumerate(bm25_hits, 1):
            print(f"  ({idx}) [{h.get('policy_id')}] {h.get('policy_title')} | {h.get('section')} | BM25 Score: {h.get('score')} | Chunk: {h.get('chunk_id')}")
    else:
        print("  None")

    print("\n[5. Vector Search Results (Top Semantic Hits)]")
    vec_hits = debug_trace.get("5. Vector Search Results", [])
    if vec_hits:
        for idx, h in enumerate(vec_hits, 1):
            print(f"  ({idx}) [{h.get('policy_id')}] {h.get('policy_title')} | {h.get('section')} | Cosine Sim: {h.get('similarity')} | Chunk: {h.get('chunk_id')}")
    else:
        print("  None")

    print("\n[6. RRF Combined Results (Fused Candidates)]")
    rrf_hits = debug_trace.get("6. RRF Combined Results", [])
    if rrf_hits:
        for idx, h in enumerate(rrf_hits, 1):
            print(f"  ({idx}) [{h.get('policy_id')}] {h.get('policy_title')} | {h.get('section')} | Cumulative RRF: {h.get('rrf_score')} | Chunk: {h.get('chunk_id')}")
    else:
        print("  None")

    print(f"\n[7. Metadata Filtering Results]\n  {debug_trace.get('7. Metadata Filtering Results', {})}")

    print("\n[8. Cross-Encoder Reranker Results (Top Ranked Candidates)]")
    rerank_hits = debug_trace.get("8. Reranker Results", [])
    if rerank_hits:
        for idx, h in enumerate(rerank_hits, 1):
            print(f"  ({idx}) [{h.get('policy_id')}] {h.get('policy_title')} | {h.get('section')} | Rerank Score: {h.get('rerank_score')} | Chunk: {h.get('chunk_id')}")
    else:
        print("  None")

    print("\n[9. Final Context Sent to LLM (Assembled & Verified Evidence)]")
    context_str = debug_trace.get("9. Final Context Sent to LLM", "")
    if context_str:
        preview_lines = context_str.splitlines()
        preview = "\n  ".join(preview_lines[:25])
        if len(preview_lines) > 25:
            preview += f"\n  ... [{len(preview_lines) - 25} more lines omitted for display]"
        print(f"  {preview}")
    else:
        print("  No context generated")

    print(f"\n[10. Final Generated Answer]\n{debug_trace.get('10. Final Generated Answer', 'N/A')}")

    print("\n[11. Citation Validation Results]")
    val_res = debug_trace.get("11. Citation Validation Results", {})
    if val_res:
        print(f"  Validation Passed: {val_res.get('is_valid', True)}")
        summary = val_res.get("validation_summary", {})
        print(f"  Software Check Passed: {summary.get('software_check_passed')}")
        print(f"  Numbers/Limits Check Passed: {summary.get('numbers_check_passed')}")
        print(f"  Verified Citations Count: {summary.get('citations_verified_count')}")
    else:
        print("  Validation summary unavailable")

    print("\n[12. Unsupported Claims Detected]")
    unsupported = debug_trace.get("12. Unsupported Claims Detected", [])
    if unsupported:
        for u in unsupported:
            print(f"  - {u}")
    else:
        print("  None (Zero ungrounded claims detected)")

    print("🔍" * 40 + "\n")


def format_query_response(result: dict, duration_ms: float, debug: bool = False):
    query = result.get("query", "")
    answer = result.get("answer", "")
    is_answerable = result.get("is_answerable", True)
    confidence = result.get("confidence", 0.0)
    citations = result.get("citations", [])
    policy_ids = result.get("policy_ids", [])
    lang = result.get("language", "en")
    debug_trace = result.get("debug_trace", {})

    if debug and debug_trace:
        display_debug_trace(debug_trace)

    print("\n" + "=" * 80)
    print(f"QUERY: {query} (Detected Language: {lang.upper()})")
    print("=" * 80)

    if not is_answerable:
        print(f"\n[NOTICE] {answer}\n")
        print(f"Confidence: {confidence:.2f} | Execution Latency: {duration_ms:.1f} ms")
        print("=" * 80 + "\n")
        return

    print("\n[ANSWER]")
    print(answer)
    print("\n" + "-" * 80)
    print(f"RELEVANT POLICIES: {', '.join(policy_ids) if policy_ids else 'None'}")
    print(f"CONFIDENCE SCORE:  {confidence:.2f} / 1.00")
    print(f"PIPELINE LATENCY:  {duration_ms:.1f} ms")

    if citations:
        print("\n[EXPLICIT CITATIONS & POLICY PROVENANCE]")
        for idx, src in enumerate(citations, start=1):
            pid = src.get("policy_id", "N/A")
            title = src.get("policy_title", "N/A")
            sec_num = src.get("section_number", "")
            sec_title = src.get("section_title", "")
            dept = src.get("department", "N/A")
            src_file = src.get("source_file", "policies/")
            score = src.get("score", src.get("relevance_score", 0.0))
            sec_str = f"Section {sec_num} ({sec_title})" if sec_num and sec_title else (sec_title or "General")
            print(f"  [{idx}] Policy {pid}: {title} (Dept: {dept})")
            print(f"      {sec_str} | Source: {src_file} | Score: {score:.4f}")
    print("=" * 80 + "\n")


def execute_single_query(query: str, department: Optional[str] = None, debug: bool = False):
    """Executes a single question answering query via the full LangGraph pipeline."""
    start_time = time.perf_counter()
    result = run_policy_rag(query, user_department=department, debug=debug)
    dur = (time.perf_counter() - start_time) * 1000.0
    format_query_response(result, dur, debug=debug)


def run_interactive_repl(debug: bool = False):
    """Runs interactive terminal chat loop."""
    print_banner()
    print("Type your policy inquiry in English or Bangla (বাংলা).")
    print("Commands:")
    print("  exit / quit         - Exit application")
    print("  /debug on|off       - Toggle retrieval debug trace")
    print("  /dept <dept_name>   - Scope subsequent queries to department (e.g. /dept HR)")
    print("  /clear_dept         - Remove active department scope")
    print("  /help               - Show available instructions\n")

    current_dept = None
    active_debug = debug

    while True:
        try:
            status_str = f"{current_dept or 'All'}{' | DEBUG' if active_debug else ''}"
            prompt_str = f"PolicyRAG [{status_str}] > "
            user_input = input(prompt_str).strip()
            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", ":q"):
                print("\nExiting Enterprise Policy RAG. Goodbye!")
                break

            if user_input.startswith("/debug"):
                parts = user_input.split()
                if len(parts) > 1 and parts[1].lower() in ("off", "false", "0"):
                    active_debug = False
                    print("[*] Retrieval debugging mode disabled.")
                else:
                    active_debug = True
                    print("[*] Retrieval debugging mode enabled.")
                continue

            if user_input.startswith("/dept"):
                parts = user_input.split(maxsplit=1)
                if len(parts) > 1:
                    current_dept = parts[1].strip()
                    print(f"[*] Department scope set to: {current_dept}")
                else:
                    print("[!] Please specify a department. (e.g., /dept HR or /dept Finance)")
                continue

            if user_input == "/clear_dept":
                current_dept = None
                print("[*] Department scope cleared. Searching across all 10 departments.")
                continue

            if user_input == "/help":
                print("\nSample queries:")
                print("  - What is the procedure for employee expense reimbursement?")
                print("  - What is FIN-002?")
                print("  - Does the company use Concur for expense reimbursement?")
                print("  - Is there a $500 reimbursement limit for ergonomic equipment?")
                print("  - What documents are required for expense reimbursement?")
                print("  - Who approves employee expense claims?")
                print("  - Explain the Finance Department's reimbursement procedure in Bangla.\n")
                continue

            execute_single_query(user_input, department=current_dept, debug=active_debug)

        except (KeyboardInterrupt, EOFError):
            print("\nExiting Enterprise Policy RAG. Goodbye!")
            break
        except Exception as e:
            print(f"\n[ERROR] An error occurred: {e}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Enterprise Policy Hybrid RAG Retrieval & QA System",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-q", "--query", type=str, help="Single query to ask the policy knowledge base")
    parser.add_argument("-d", "--dept", type=str, help="Filter search to specific department")
    parser.add_argument("--debug", action="store_true", help="Enable 11-point Retrieval Debugging Mode")
    parser.add_argument("--index", action="store_true", help="Re-index all 150 enterprise policy documents")
    parser.add_argument("--eval", action="store_true", help="Run 7-architecture benchmark evaluation")
    parser.add_argument("--api", action="store_true", help="Launch FastAPI application server")
    parser.add_argument("--port", type=int, default=8000, help="Port for FastAPI server (default: 8000)")

    args = parser.parse_args()

    if args.index:
        print_banner()
        print("[*] Starting full enterprise policy ingestion and indexing...")
        from src.ingestion.indexer import EnterprisePolicyIndexer
        indexer = EnterprisePolicyIndexer()
        indexer.run()
        print("[+] Indexing complete!")
        return

    if args.eval:
        print_banner()
        from src.evaluation.evaluate import run_evaluation, print_summary_table, generate_markdown_report
        from src.config.settings import settings
        report_file = Path("data/processed/evaluation_report.md")
        results = run_evaluation(top_k=settings.FINAL_TOP_K)
        print_summary_table(results)
        generate_markdown_report(results, report_file)
        return

    if args.api:
        import uvicorn
        print(f"[*] Starting Enterprise Policy RAG API server on port {args.port}...")
        uvicorn.run("src.api.main:app", host="0.0.0.0", port=args.port, reload=False)
        return

    if args.query:
        execute_single_query(args.query, department=args.dept, debug=args.debug)
    else:
        run_interactive_repl(debug=args.debug)


if __name__ == "__main__":
    main()
