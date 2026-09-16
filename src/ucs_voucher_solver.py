import heapq
from typing import Dict, List, Tuple

# Validasi Pustaka Stack AI Utama (Sesuai Environment Setup Guide)
import chromadb
import cv2
import gradio as gr
import numpy as np
import pandas as pd
import sklearn
from google import genai
from pydantic import BaseModel


# 1. Model Data Voucher BelanjaHemat
class Voucher(BaseModel):
    code: str
    category: str  # 'direct_discount', 'cashback', 'ongkir'
    discount_type: str  # 'flat' atau 'percent'
    discount_value: float
    min_purchase: float = 0.0
    max_discount: float = float("inf")

    def calculate_discount(self, current_total: float) -> float:
        """Menghitung nominal potongan harga berdasarkan aturan voucher."""
        if current_total < self.min_purchase:
            return 0.0

        if self.discount_type == "flat":
            discount = self.discount_value
        elif self.discount_type == "percent":
            discount = current_total * (self.discount_value / 100.0)
        else:
            discount = 0.0

        return min(discount, self.max_discount)


# 2. Solver UCS dengan Aturan Stacking BelanjaHemat
def ucs_voucher_optimization(
    initial_cart_total: float, available_vouchers: List[Voucher]
) -> Tuple[float, List[str]]:
    """Optimasi Kombinasi Voucher BelanjaHemat menggunakan Uniform Cost Search (UCS)."""
    # Priority Queue menyimpan: (current_cost, tuple_kode_voucher_terpakai)
    pq: List[Tuple[float, Tuple[str, ...]]] = []
    heapq.heappush(pq, (initial_cart_total, ()))

    visited_costs: Dict[Tuple[str, ...], float] = {(): initial_cart_total}
    best_cost = initial_cart_total
    best_combination: List[str] = []

    while pq:
        current_cost, used_vouchers = heapq.heappop(pq)

        if current_cost < best_cost:
            best_cost = current_cost
            best_combination = list(used_vouchers)

        # Cek kategori voucher yang sudah terpakai di state ini
        used_categories = [
            v.category
            for v in available_vouchers
            if v.code in used_vouchers
        ]

        for voucher in available_vouchers:
            # Aturan Stacking: 'direct_discount' tidak boleh digabung sesama 'direct_discount'
            is_valid_stack = True
            if (
                voucher.category == "direct_discount"
                and "direct_discount" in used_categories
            ):
                is_valid_stack = False

            if voucher.code not in used_vouchers and is_valid_stack:
                discount = voucher.calculate_discount(current_cost)
                if discount > 0:
                    new_cost = max(0.0, current_cost - discount)
                    new_used_vouchers = tuple(
                        sorted(list(used_vouchers) + [voucher.code])
                    )

                    if (
                        new_used_vouchers not in visited_costs
                        or new_cost < visited_costs[new_used_vouchers]
                    ):
                        visited_costs[new_used_vouchers] = new_cost
                        heapq.heappush(pq, (new_cost, new_used_vouchers))

    return best_cost, best_combination


# 3. Eksekusi Pengujian Skenario BelanjaHemat
if __name__ == "__main__":
    print(
        "[INFO] Validasi Stack AI: Seluruh pustaka utama berhasil dimuat!\n"
    )

    # Voucher dengan Penamaan Populer & Menarik
    belanja_vouchers = [
        Voucher(
            code="PAYDAY_BIGSALE_20",
            category="direct_discount",
            discount_type="percent",
            discount_value=20,
            min_purchase=200000,
            max_discount=50000,
        ),
        Voucher(
            code="MANTAP_DEAL_30K",
            category="direct_discount",
            discount_type="flat",
            discount_value=30000,
            min_purchase=150000,
        ),
        Voucher(
            code="EXTRA_CASHBACK_10",
            category="cashback",
            discount_type="percent",
            discount_value=10,
            min_purchase=0,
            max_discount=25000,
        ),
        Voucher(
            code="BEBAS_ONGKIR_SUPER",
            category="ongkir",
            discount_type="flat",
            discount_value=20000,
            min_purchase=0,
        ),
    ]

    cart_total = 500000.0
    final_price, applied_vouchers = ucs_voucher_optimization(
        cart_total, belanja_vouchers
    )

    print("==================================================")
    print("   AI COPILOT OPTIMASI VOUCHER BELANJAHEMAT (UCS) ")
    print("==================================================")
    print(f"Total Keranjang Awal : Rp {cart_total:,.2f}")
    print(f"Harga Akhir Optimal  : Rp {final_price:,.2f}")
    print(f"Total Penghematan    : Rp {(cart_total - final_price):,.2f}")
    print(f"Kombinasi Voucher    : {applied_vouchers}")
    print("==================================================")