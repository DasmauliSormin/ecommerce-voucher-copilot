import argparse
import json
import os
import sys

# Menambahkan direktori folder src ke sys.path agar Pylance & Python menemukan modul
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)

# Import langsung dari csp_solver.py
from csp_solver import VoucherCSPSolver


def load_dataset(file_path: str):
    """Membaca dataset JSON voucher dari folder data/."""
    if not os.path.exists(file_path):
        # Cek path relatif jika dijalankan dari root direktori proyek
        alt_path = os.path.join(CURRENT_DIR, "..", file_path)
        if os.path.exists(alt_path):
            file_path = alt_path
        else:
            print(f"[ERROR] File dataset '{file_path}' tidak ditemukan!")
            sys.exit(1)

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_benchmark_comparison(vouchers_data: list, total_belanja: float):
    """Menjalankan evaluasi CSP Backtracking & mencetak ringkasan hasil."""
    solver = VoucherCSPSolver(vouchers_data, total_belanja)
    selected_vouchers, total_benefit, exec_time = solver.solve_backtracking()

    print("\n========================================================================")
    print("=== AI COPILOT OPTIMASI VOUCHER - MILESTONE 2 (CSP SOLVER) ===")
    print("========================================================================")
    print(f"Total Belanja Keranjang   : Rp {total_belanja:,.2f}")
    print(f"Jumlah Voucher di Katalog : {solver.num_vouchers}")
    print(f"Node Dieksplorasi          : {solver.nodes_explored}")
    print(f"Cabang Terpangkas (Pruned) : {solver.pruned_count}")
    print(f"Waktu Komputasi            : {exec_time * 1000:.3f} ms")
    print("------------------------------------------------------------------------")
    print("STATUS SOLVER: OPTIMAL (AC-3 + Backtracking MRV + Branch & Bound)")
    print("------------------------------------------------------------------------")

    if not selected_vouchers or total_benefit == 0:
        print("Tidak ada kombinasi voucher yang memenuhi syarat/valid.")
    else:
        print("Voucher Terpilih:")
        for idx, v in enumerate(selected_vouchers, 1):
            benefit = solver.calculate_single_benefit(v)
            print(f"  {idx}. [{v['code']}] {v['category'].upper()} -> Hemat Rp {benefit:,.2f}")

        total_bayar = max(0.0, total_belanja - total_benefit)
        print("------------------------------------------------------------------------")
        print(f"Total Penghematan       : Rp {total_benefit:,.2f}")
        print(f"Total Bayar di Checkout : Rp {total_bayar:,.2f}")
    print("========================================================================\n")


def run_m1_regression():
    """Uji Regresi Skenario Milestone 1 (4 Voucher, Total Belanja Rp 500.000)."""
    print("\n[INFO] Menjalankan Uji Regresi Skenario Milestone 1...")
    m1_vouchers = [
        {
            "id": "V1",
            "code": "PAYDAY_BIGSALE_20",
            "category": "direct_discount",
            "discount_type": "percent",
            "discount_value": 20,
            "min_purchase": 200000,
            "max_discount": 50000,
            "mutually_exclusive_with": ["direct_discount"],
        },
        {
            "id": "V2",
            "code": "MANTAP_DEAL_30K",
            "category": "direct_discount",
            "discount_type": "flat",
            "discount_value": 30000,
            "min_purchase": 150000,
            "max_discount": 30000,
            "mutually_exclusive_with": ["direct_discount"],
        },
        {
            "id": "V3",
            "code": "EXTRA_CASHBACK_10",
            "category": "cashback",
            "discount_type": "percent",
            "discount_value": 10,
            "min_purchase": 0,
            "max_discount": 25000,
            "mutually_exclusive_with": [],
        },
        {
            "id": "V4",
            "code": "BEBAS_ONGKIR_SUPER",
            "category": "free_shipping",
            "discount_type": "flat",
            "discount_value": 20000,
            "min_purchase": 0,
            "max_discount": 20000,
            "mutually_exclusive_with": [],
        },
    ]
    run_benchmark_comparison(m1_vouchers, total_belanja=500000.0)


def main():
    parser = argparse.ArgumentParser(description="Runner CLI untuk CSPSolver Optimasi Voucher")
    parser.add_argument("--scenario", choices=["main", "m1"], default="main", help="Pilih skenario: 'main' atau 'm1'")
    parser.add_argument("--dataset", default="data/vouchers_real.json", help="Path ke dataset JSON")
    args = parser.parse_args()

    if args.scenario == "m1":
        run_m1_regression()
    else:
        vouchers_data = load_dataset(args.dataset)
        try:
            user_input = input("Masukkan Total Belanja Keranjang (Rp) [Default 500000]: ")
            total_belanja = float(user_input) if user_input.strip() else 500000.0
        except ValueError:
            print("[WARN] Input tidak valid, menggunakan nilai default Rp 500.000")
            total_belanja = 500000.0

        run_benchmark_comparison(vouchers_data, total_belanja)


if __name__ == "__main__":
    main()