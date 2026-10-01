import os
import sys
import pytest

# Menambahkan path folder src agar modul csp_solver dapat di-import dengan mulus
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(CURRENT_DIR, "..", "src")
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)

from csp_solver import VoucherCSPSolver


@pytest.fixture
def sample_vouchers():
    """Fixture menyediakan dataset voucher untuk pengujian."""
    return [
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


def test_m1_regression_scenario(sample_vouchers):
    """Uji Regresi Milestone 1: Keranjang Rp 500.000 memilih V1, V3, dan V4 (Total hemat Rp 95.000)."""
    solver = VoucherCSPSolver(sample_vouchers, total_belanja=500000.0)
    selected_vouchers, total_benefit, _ = solver.solve_backtracking()

    assert total_benefit == 95000.0
    assert len(selected_vouchers) == 3
    selected_codes = [v["code"] for v in selected_vouchers]
    assert "PAYDAY_BIGSALE_20" in selected_codes
    assert "EXTRA_CASHBACK_10" in selected_codes
    assert "BEBAS_ONGKIR_SUPER" in selected_codes


def test_min_purchase_constraint(sample_vouchers):
    """Pengujian Batasan Unary: Jika total belanja di bawah minimum purchase, voucher dieliminasi."""
    # Total belanja Rp 100.000 -> V1 (min Rp 200rb) dan V2 (min Rp 150rb) tidak berlaku
    solver = VoucherCSPSolver(sample_vouchers, total_belanja=100000.0)
    selected_vouchers, total_benefit, _ = solver.solve_backtracking()

    selected_codes = [v["code"] for v in selected_vouchers]
    assert "PAYDAY_BIGSALE_20" not in selected_codes
    assert "MANTAP_DEAL_30K" not in selected_codes


def test_mutually_exclusive_constraint(sample_vouchers):
    """Pengujian Batasan Biner: V1 dan V2 saling eksklusif, solver wajib memilih yang memberikan benefit terbesar (V1)."""
    solver = VoucherCSPSolver(sample_vouchers, total_belanja=500000.0)
    selected_vouchers, _, _ = solver.solve_backtracking()

    selected_codes = [v["code"] for v in selected_vouchers]
    # Memastikan tidak ada dua voucher direct_discount yang terpilih bersamaan
    assert not ("PAYDAY_BIGSALE_20" in selected_codes and "MANTAP_DEAL_30K" in selected_codes)


def test_empty_cart():
    """Pengujian Edge Case: Keranjang belanja Rp 0 tidak mengembalikan voucher apa pun."""
    vouchers = [
        {
            "id": "V1",
            "code": "DISC10",
            "category": "direct_discount",
            "discount_type": "percent",
            "discount_value": 10,
            "min_purchase": 50000,
            "max_discount": 10000,
            "mutually_exclusive_with": [],
        }
    ]
    solver = VoucherCSPSolver(vouchers, total_belanja=0.0)
    selected_vouchers, total_benefit, _ = solver.solve_backtracking()

    assert len(selected_vouchers) == 0
    assert total_benefit == 0.0