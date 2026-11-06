import json
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
KB_DIR = os.path.join(CURRENT_DIR, "ecommerce_voucher_copilot", "knowledge_base")

for p in [CURRENT_DIR, KB_DIR, PROJECT_ROOT]:
  if p not in sys.path:
    sys.path.insert(0, p)

try:
  from retriever import retrieve_context
except ImportError:
  try:
    from ecommerce_voucher_copilot.knowledge_base.retriever import (
        retrieve_context,
    )
  except ImportError:
    from src.ecommerce_voucher_copilot.knowledge_base.retriever import (
        retrieve_context,
    )


def run_benchmark():
  queries_path = os.path.join(PROJECT_ROOT, "Data", "queries.json")
  report_dir = os.path.join(PROJECT_ROOT, "reports")
  os.makedirs(report_dir, exist_ok=True)

  if not os.path.exists(queries_path):
    print(f"[!] File queries.json tidak ditemukan di: {queries_path}")
    return

  with open(queries_path, "r", encoding="utf-8") as f:
    queries = json.load(f)

  results_summary = []
  print("=" * 70)
  print("   BENCHMARK EVALUATOR (GRUP 16 - RETRIEVAL ACCURACY & OOD REJECTION)")
  print("=" * 70)

  for item in queries:
    qid = item["id"]
    qtype = item["type"]
    qtext = item["query"]

    retrieved = retrieve_context(qtext, top_k=1)
    top_res = retrieved[0] if retrieved else None

    sim_score = top_res.get("cosine_similarity", 0.0) if top_res else 0.0
    accepted = top_res.get("is_accepted", False) if top_res else False

    is_ood = "OOD" in qtype.upper()
    
    if is_ood:
      # Untuk OOD, sukses jika ditolak (accepted = False / di bawah threshold)
      status = "PASSED" if not accepted else "FAILED"
    else:
      # Untuk Literal, Sinonim, Ambigu, sukses jika skor >= 0.35 (atau accepted = True)
      status = "PASSED" if (sim_score >= 0.35 or accepted) else "FAILED"

    print(
        f"[{qid}] Tipe: {qtype:15s} | Sim Score: {sim_score:.4f} | Status:"
        f" {status}"
    )

    results_summary.append({
        "id": qid,
        "type": qtype,
        "query": qtext,
        "similarity_score": sim_score,
        "is_accepted": accepted,
        "status": status,
        "matched_source": top_res.get("metadata", {}).get("file_sumber")
        if top_res
        else None,
    })

  output_file = os.path.join(report_dir, "benchmark_results.json")
  with open(output_file, "w", encoding="utf-8") as f:
    json.dump(results_summary, f, indent=2, ensure_ascii=False)

  print("=" * 70)
  print(f"[+] Laporan benchmark berhasil disimpan di: {output_file}")


if __name__ == "__main__":
  run_benchmark()