"""
BERKELANA TRAVEL
Database Sistem Administrasi Loket Kasir
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime

DB_PATH = Path(__file__).resolve().with_name("berkelana.db")

RUTE_DEFAULT = [
    ("Semarang", "Pati", 85000),
    ("Semarang", "Jepara", 75000),
    ("Semarang", "Kudus", 80000),
    ("Semarang", "Solo", 75000),
    ("Semarang", "Yogyakarta", 85000),
]

KURSI = [f"K{i}" for i in range(1, 9)]


@contextmanager
def koneksi():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 15000")

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _ambil_semua(query, params=()):
    with koneksi() as conn:
        return [dict(row) for row in conn.execute(query, params).fetchall()]


def init_db():
    """Membuat dan memperbarui struktur database tanpa reset data."""

    with koneksi() as conn:
        rute_sudah_ada = conn.execute("""
            SELECT 1 FROM sqlite_master
            WHERE type = 'table' AND name = 'rute'
        """).fetchone()

        conn.execute("""
            CREATE TABLE IF NOT EXISTS pelanggan (
                id_pelanggan INTEGER PRIMARY KEY AUTOINCREMENT,
                nama_pelanggan TEXT NOT NULL,
                nomor_telepon TEXT NOT NULL,
                alamat TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS rute (
                id_rute INTEGER PRIMARY KEY AUTOINCREMENT,
                kota_asal TEXT NOT NULL,
                kota_tujuan TEXT NOT NULL,
                harga_tiket INTEGER NOT NULL CHECK(harga_tiket > 0),
                aktif INTEGER NOT NULL DEFAULT 1 CHECK(aktif IN (0, 1))
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS pemesanan (
                id_pemesanan INTEGER PRIMARY KEY AUTOINCREMENT,
                id_pelanggan INTEGER NOT NULL,
                id_rute INTEGER NOT NULL,
                tanggal_keberangkatan TEXT NOT NULL,
                jam_keberangkatan TEXT NOT NULL,
                harga_saat_pesan INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(id_pelanggan)
                    REFERENCES pelanggan(id_pelanggan),
                FOREIGN KEY(id_rute)
                    REFERENCES rute(id_rute)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS detail_kursi (
                id_detail INTEGER PRIMARY KEY AUTOINCREMENT,
                id_pemesanan INTEGER NOT NULL,
                nomor_kursi TEXT NOT NULL,
                FOREIGN KEY(id_pemesanan)
                    REFERENCES pemesanan(id_pemesanan)
                    ON DELETE CASCADE
            )
        """)

        # Perbaikan otomatis untuk database versi lama.
        kolom = {
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(pemesanan)"
            ).fetchall()
        }

        if "harga_saat_pesan" not in kolom:
            conn.execute("""
                ALTER TABLE pemesanan
                ADD COLUMN harga_saat_pesan INTEGER
                NOT NULL DEFAULT 0
            """)

        kolom_rute = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(rute)").fetchall()
        }
        if "aktif" not in kolom_rute:
            conn.execute("""
                ALTER TABLE rute
                ADD COLUMN aktif INTEGER NOT NULL DEFAULT 1
                CHECK(aktif IN (0, 1))
            """)

        if not rute_sudah_ada:
            conn.executemany("""
                INSERT INTO rute (kota_asal, kota_tujuan, harga_tiket)
                VALUES (?, ?, ?)
            """, RUTE_DEFAULT)

        rute_yogyakarta = conn.execute("""
            SELECT id_rute FROM rute
            WHERE LOWER(kota_asal) = 'semarang'
              AND LOWER(kota_tujuan) = 'yogyakarta'
            LIMIT 1
        """).fetchone()

        if rute_yogyakarta:
            id_yogyakarta = rute_yogyakarta["id_rute"]
        else:
            rute_lama = conn.execute("""
                SELECT id_rute FROM rute
                WHERE LOWER(kota_asal) = 'semarang'
                  AND LOWER(kota_tujuan) IN (
                      'jogjakarta', 'yogyakarta (via tol)'
                  )
                ORDER BY CASE LOWER(kota_tujuan)
                    WHEN 'jogjakarta' THEN 0 ELSE 1
                END
                LIMIT 1
            """).fetchone()
            id_yogyakarta = rute_lama["id_rute"] if rute_lama else None

            if id_yogyakarta:
                conn.execute(
                    "UPDATE rute SET kota_tujuan = 'Yogyakarta' "
                    "WHERE id_rute = ?",
                    (id_yogyakarta,)
                )

        if id_yogyakarta:
            rute_duplikat = conn.execute("""
                SELECT id_rute FROM rute
                WHERE LOWER(kota_asal) = 'semarang'
                  AND LOWER(kota_tujuan) IN (
                      'jogjakarta', 'yogyakarta (via tol)'
                  )
                  AND id_rute != ?
            """, (id_yogyakarta,)).fetchall()

            for rute in rute_duplikat:
                conn.execute(
                    "UPDATE pemesanan SET id_rute = ? WHERE id_rute = ?",
                    (id_yogyakarta, rute["id_rute"])
                )
                conn.execute(
                    "DELETE FROM rute WHERE id_rute = ?",
                    (rute["id_rute"],)
                )

        # Estimasi harga transaksi lama berdasarkan tarif rute.
        conn.execute("""
            UPDATE pemesanan
            SET harga_saat_pesan = COALESCE(
                (
                    SELECT CAST(r.harga_tiket AS INTEGER)
                    FROM rute r
                    WHERE r.id_rute = pemesanan.id_rute
                ), 0
            )
            WHERE harga_saat_pesan = 0
        """)

        # Normalisasi jam dan nomor kursi dari versi lama.
        conn.execute("""
            UPDATE pemesanan
            SET jam_keberangkatan = SUBSTR(jam_keberangkatan, 1, 5)
            WHERE jam_keberangkatan LIKE '__:__%'
              AND LENGTH(jam_keberangkatan) > 5
        """)

        conn.executemany("""
            UPDATE detail_kursi
            SET nomor_kursi = ?
            WHERE nomor_kursi LIKE ?
        """, [(f"K{nomor}", f"Kursi {nomor} (%") for nomor in range(1, 9)])

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_jadwal
            ON pemesanan(
                id_rute, tanggal_keberangkatan, jam_keberangkatan
            )
        """)


# ==========================================
# PELANGGAN
# ==========================================

def tambah_pelanggan(nama, telepon):
    nama = nama.strip()
    telepon = telepon.strip()

    if not nama or not telepon:
        raise ValueError("Nama dan nomor telepon wajib diisi.")

    if not telepon.isascii() or not telepon.isdigit():
        raise ValueError("Harus diisi dalam angka")

    with koneksi() as conn:
        duplikat = conn.execute("""
            SELECT id_pelanggan FROM pelanggan
            WHERE LOWER(nama_pelanggan) = LOWER(?)
              AND nomor_telepon = ?
            LIMIT 1
        """, (nama, telepon)).fetchone()

        if duplikat:
            return duplikat["id_pelanggan"], True

        cur = conn.execute("""
            INSERT INTO pelanggan
            (nama_pelanggan, nomor_telepon, alamat)
            VALUES (?, ?, ?)
        """, (nama, telepon, ""))

        return cur.lastrowid, False


def daftar_pelanggan():
    return _ambil_semua("""
        SELECT * FROM pelanggan
        ORDER BY id_pelanggan DESC
    """)


# ==========================================
# RUTE
# ==========================================

def daftar_rute(aktif_saja=False):
    query = "SELECT * FROM rute"
    if aktif_saja:
        query += " WHERE aktif = 1"
    return _ambil_semua(query + " ORDER BY id_rute")


def tambah_rute(asal, tujuan, harga):
    asal, tujuan = asal.strip(), tujuan.strip()

    if not asal or not tujuan:
        raise ValueError("Kota asal dan tujuan wajib diisi.")
    if asal.casefold() == tujuan.casefold():
        raise ValueError("Kota asal dan tujuan tidak boleh sama.")

    try:
        harga = int(harga)
    except (TypeError, ValueError):
        raise ValueError("Harga tiket harus berupa angka.") from None

    if harga <= 0:
        raise ValueError("Harga tiket harus lebih dari nol.")

    with koneksi() as conn:
        ada = conn.execute("""
            SELECT 1 FROM rute
            WHERE LOWER(kota_asal) = LOWER(?)
              AND LOWER(kota_tujuan) = LOWER(?)
        """, (asal, tujuan)).fetchone()

        if ada:
            raise ValueError("Rute tersebut sudah terdaftar.")

        cur = conn.execute("""
            INSERT INTO rute (kota_asal, kota_tujuan, harga_tiket)
            VALUES (?, ?, ?)
        """, (asal, tujuan, harga))
        return cur.lastrowid


def hapus_rute(id_rute):
    with koneksi() as conn:
        ada = conn.execute(
            "SELECT 1 FROM rute WHERE id_rute = ?", (id_rute,)
        ).fetchone()
        if not ada:
            return False

        dipakai = conn.execute("""
            SELECT 1 FROM pemesanan WHERE id_rute = ? LIMIT 1
        """, (id_rute,)).fetchone()
        if dipakai:
            raise ValueError("Rute yang sudah memiliki transaksi tidak dapat dihapus.")

        conn.execute("DELETE FROM rute WHERE id_rute = ?", (id_rute,))
        return True


def set_status_rute(id_rute, aktif):
    with koneksi() as conn:
        cur = conn.execute(
            "UPDATE rute SET aktif = ? WHERE id_rute = ?",
            (int(aktif), id_rute)
        )
        return cur.rowcount > 0


# ==========================================
# KURSI DAN PEMESANAN
# ==========================================

def get_kursi_terpesan(tanggal, jam, id_rute):
    with koneksi() as conn:
        rows = conn.execute("""
            SELECT dk.nomor_kursi
            FROM detail_kursi dk
            JOIN pemesanan p
              ON dk.id_pemesanan = p.id_pemesanan
            WHERE p.id_rute = ?
              AND p.tanggal_keberangkatan = ?
              AND SUBSTR(p.jam_keberangkatan, 1, 5) = ?
        """, (id_rute, str(tanggal), str(jam)[:5])).fetchall()

        return [r["nomor_kursi"] for r in rows]


def tambah_pemesanan(
    id_pelanggan, id_rute, tanggal, jam, daftar_kursi
):
    tanggal = str(tanggal)
    jam = str(jam)[:5]
    daftar_kursi = list(daftar_kursi)

    if not daftar_kursi:
        raise ValueError("Pilih minimal satu kursi.")

    if len(daftar_kursi) != len(set(daftar_kursi)):
        raise ValueError("Ada nomor kursi yang duplikat.")

    if any(k not in KURSI for k in daftar_kursi):
        raise ValueError("Nomor kursi tidak valid.")

    try:
        jadwal = datetime.strptime(
            f"{tanggal} {jam}", "%Y-%m-%d %H:%M"
        )
    except ValueError:
        raise ValueError("Format jadwal tidak valid.")

    if jadwal < datetime.now():
        raise ValueError("Jadwal keberangkatan sudah berlalu.")

    with koneksi() as conn:
        # Mencegah dua transaksi mengambil kursi bersamaan.
        conn.execute("BEGIN IMMEDIATE")

        pelanggan = conn.execute("""
            SELECT id_pelanggan FROM pelanggan
            WHERE id_pelanggan = ?
        """, (id_pelanggan,)).fetchone()

        if not pelanggan:
            raise ValueError("Pelanggan tidak ditemukan.")

        rute = conn.execute("""
            SELECT harga_tiket FROM rute
            WHERE id_rute = ? AND aktif = 1
        """, (id_rute,)).fetchone()

        if not rute:
            raise ValueError("Rute tidak ditemukan atau sudah nonaktif.")

        rows = conn.execute("""
            SELECT dk.nomor_kursi
            FROM detail_kursi dk
            JOIN pemesanan p
              ON dk.id_pemesanan = p.id_pemesanan
            WHERE p.id_rute = ?
              AND p.tanggal_keberangkatan = ?
              AND SUBSTR(p.jam_keberangkatan, 1, 5) = ?
        """, (id_rute, tanggal, jam)).fetchall()

        terpakai = {r["nomor_kursi"] for r in rows}
        konflik = [k for k in daftar_kursi if k in terpakai]

        if konflik:
            raise ValueError(
                "Kursi sudah terpesan: " + ", ".join(konflik)
            )

        harga = int(rute["harga_tiket"])

        cur = conn.execute("""
            INSERT INTO pemesanan (
                id_pelanggan, id_rute,
                tanggal_keberangkatan, jam_keberangkatan,
                harga_saat_pesan
            ) VALUES (?, ?, ?, ?, ?)
        """, (id_pelanggan, id_rute, tanggal, jam, harga))

        id_order = cur.lastrowid

        conn.executemany("""
            INSERT INTO detail_kursi (id_pemesanan, nomor_kursi)
            VALUES (?, ?)
        """, [(id_order, k) for k in daftar_kursi])

        return id_order


# ==========================================
# RIWAYAT DAN STATISTIK
# ==========================================

def daftar_pemesanan():
    return _ambil_semua("""
            SELECT
                p.id_pemesanan,
                c.nama_pelanggan,
                c.nomor_telepon,
                c.alamat,
                r.kota_asal,
                r.kota_tujuan,
                p.harga_saat_pesan AS harga_tiket,
                p.tanggal_keberangkatan,
                p.jam_keberangkatan,
                GROUP_CONCAT(dk.nomor_kursi, ', ') AS kursi_dipesan,
                COUNT(dk.id_detail) AS jumlah_tiket,
                COUNT(dk.id_detail) * p.harga_saat_pesan
                    AS total_harga
            FROM pemesanan p
            JOIN pelanggan c
              ON p.id_pelanggan = c.id_pelanggan
            JOIN rute r
              ON p.id_rute = r.id_rute
            LEFT JOIN detail_kursi dk
              ON p.id_pemesanan = dk.id_pemesanan
            GROUP BY p.id_pemesanan
            ORDER BY p.id_pemesanan DESC
        """)


def hapus_pemesanan(id_pemesanan):
    with koneksi() as conn:
        cur = conn.execute("""
            DELETE FROM pemesanan WHERE id_pemesanan = ?
        """, (id_pemesanan,))

        return cur.rowcount > 0


def total_statistik():
    with koneksi() as conn:
        return tuple(conn.execute("""
            SELECT
                (SELECT COUNT(*) FROM pelanggan),
                (SELECT COUNT(*) FROM pemesanan),
                (SELECT COUNT(*) FROM rute)
        """).fetchone())


def total_pendapatan():
    with koneksi() as conn:
        hasil = conn.execute("""
            SELECT COALESCE(SUM(p.harga_saat_pesan), 0)
            FROM detail_kursi dk
            JOIN pemesanan p
              ON dk.id_pemesanan = p.id_pemesanan
        """).fetchone()[0]

        return int(hasil)


if __name__ == "__main__":
    init_db()
    print("Database BERKELANA TRAVEL siap digunakan.")