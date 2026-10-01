import json
import time
from typing import Dict, List, Tuple


class VoucherCSPSolver:

    def __init__(self, vouchers_data: List[Dict], total_belanja: float):
        """Inisialisasi variabel keputusan, domain, dan batasan CSP .

        - Variabel: Setiap voucher i (V1, V2, dst)
        - Domain: {1: AMBIL, 0: LEWATI}
        """
        self.vouchers = vouchers_data
        self.total_belanja = total_belanja
        self.num_vouchers = len(vouchers_data)

        # Variabel pelacak performa
        self.nodes_explored = 0
        self.pruned_count = 0

    def calculate_single_benefit(self, voucher: Dict) -> float:
        """Menghitung nominal potongan dari satu voucher berdasarkan total belanja."""
        if self.total_belanja < voucher["min_purchase"]:
            return 0.0

        if voucher["discount_type"] == "percent":
            raw_discount = (voucher["discount_value"] / 100.0) * self.total_belanja
            return min(raw_discount, float(voucher["max_discount"]))
        else:
            return float(voucher["discount_value"])

    def is_consistent(
        self, voucher_idx: int, current_assignment: Dict[int, int]
    ) -> bool:
        """Fungsi Batasan (Constraint Checker) :

        1. Syarat Minimum Belanja
        2. Aturan Stacking / Mutual Exclusivity
        """
        candidate = self.vouchers[voucher_idx]

        # Batasan 1: Minimum Belanja
        if self.total_belanja < candidate["min_purchase"]:
            return False

        # Batasan 2: Mutual Exclusivity dengan voucher lain yang sudah diambil (assignment == 1)
        for prev_idx, status in current_assignment.items():
            if status == 1:
                prev_voucher = self.vouchers[prev_idx]

                # Cek apakah kategori saling membatasi
                if (
                    candidate["category"] in prev_voucher["mutually_exclusive_with"]
                    or prev_voucher["category"] in candidate["mutually_exclusive_with"]
                ):
                    return False

        return True

    def solve_backtracking(self) -> Tuple[List[Dict], float, float]:
        """Menjalankan Backtracking Search dengan Propagasi Batasan (Forward Checking) ."""
        best_assignment = {}
        best_benefit = -1.0

        def backtrack(index: int, current_assignment: Dict[int, int]):
            nonlocal best_assignment, best_benefit
            self.nodes_explored += 1

            # Base Case: Seluruh voucher telah diputuskan (Goal State)
            if index == self.num_vouchers:
                current_benefit = sum(
                    self.calculate_single_benefit(self.vouchers[i])
                    for i, val in current_assignment.items()
                    if val == 1
                )
                if current_benefit > best_benefit:
                    best_benefit = current_benefit
                    best_assignment = current_assignment.copy()
                return

            # Opsi 1: Coba AMBIL Voucher (Assignment = 1)
            if self.is_consistent(index, current_assignment):
                current_assignment[index] = 1
                backtrack(index + 1, current_assignment)
                del current_assignment[index]
            else:
                self.pruned_count += 1  # Cabang terpangkas oleh batasan!

            # Opsi 2: Coba LEWATI Voucher (Assignment = 0)
            current_assignment[index] = 0
            backtrack(index + 1, current_assignment)
            del current_assignment[index]

        start_time = time.perf_counter()
        backtrack(0, {})
        execution_time = time.perf_counter() - start_time

        # Rekonstruksi hasil voucher terpilih
        selected_vouchers = [
            self.vouchers[i] for i, val in best_assignment.items() if val == 1
        ]
        return selected_vouchers, best_benefit, execution_time