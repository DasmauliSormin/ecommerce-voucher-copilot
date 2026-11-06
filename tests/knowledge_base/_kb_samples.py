"""Teks contoh korpus untuk unit test."""

DOC_STACKING = """# Kebijakan Umum Voucher dan Aturan Penggabungan

## 1. Tujuan
Dokumen ini mengatur penggabungan voucher di BelanjaHemat. Kebijakan berlaku untuk seluruh pengguna.

## 3. Ketentuan
### 3.2 Aturan Stacking
1. Voucher diskon platform tidak dapat digabung dengan voucher toko. Hal ini berlaku sejak 1 Januari 2026.
2. Voucher gratis ongkos kirim dapat digabung dengan cashback, dll. sesuai No. 3 di bawah.
3. Maksimum tiga voucher per transaksi.

## 4. Sanksi
Penyalahgunaan voucher dikenai pemblokiran akun.
"""

DOC_COD = """# Kebijakan Metode Pembayaran

## 2. Batas COD
Transaksi COD dibatasi maksimal Rp1.000.000 per pesanan. Voucher cashback e-wallet tidak berlaku untuk COD.

## 3. E-Wallet
Cashback GOPAY hanya diberikan jika pembayaran memakai GOPAY. Minimum belanja dihitung setelah diskon platform.
"""

CATALOG = """doc_id,file_sumber,judul,nomor_dokumen,versi,tanggal_berlaku,departemen,jenis_dokumen,kategori_voucher,kode_batasan_terkait
KB01,kb01_stacking.md,Kebijakan Umum Voucher dan Aturan Penggabungan,BH/KBJ/MKT/001/2026,1.0,2026-01-01,Marketing,Kebijakan,UMUM,"B3,B4,G3"
KB06,kb06_pembayaran.txt,Kebijakan Metode Pembayaran,BH/KBJ/PAY/006/2026,1.1,2026-02-01,Payment,Kebijakan,PEMBAYARAN,"U5,U6,B1"
"""
