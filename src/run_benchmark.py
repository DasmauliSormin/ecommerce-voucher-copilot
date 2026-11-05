import os
import json
from retriever import retrieve_context

def run_benchmark():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    queries_path = os.path.join(base_dir, "Data", "queries.json")
    report_dir = os.path.join(base_dir, "reports")
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
        
        sim_score = top_res["cosine_similarity"] if top_res else 0.0
        accepted = top_res["is_accepted"] if top_res else False

        # Evaluasi Status:
        # - Jika kueri mengandung 'OOD' (Out-of-Domain), PASSED diperoleh jika DITOLAK (accepted == False)
        # - Jika kueri domain bisnis (Literal, Sinonim, Ambigu), PASSED diperoleh jika DITERIMA (accepted == True)
        is_ood = "OOD" in qtype.upper()
        if is_ood:
            status = "PASSED" if not accepted else "FAILED"
        else:
            status = "PASSED" if accepted else "FAILED"

        print(f"[{qid}] Tipe: {qtype:15s} | Sim Score: {sim_score:.4f} | Status: {status}")
        
        results_summary.append({
            "id": qid,
            "type": qtype,
            "query": qtext,
            "similarity_score": sim_score,
            "is_accepted": accepted,
            "status": status,
            "matched_source": top_res["metadata"]["source"] if top_res else None
        })

    output_file = os.path.join(report_dir, "benchmark_results.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2)
        
    print("=" * 70)
    print(f"[+] Laporan benchmark berhasil disimpan di: {output_file}")

if __name__ == "__main__":
    run_benchmark()