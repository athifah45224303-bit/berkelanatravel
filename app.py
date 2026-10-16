"""
BERKELANA TRAVEL
Sistem Administrasi Loket Kasir
Your Journey, Our Care.
"""

import streamlit as st
import database as db
import pandas as pd
from datetime import date
from pathlib import Path
import base64
import html

# ==========================================
# KONFIGURASI
# ==========================================

st.set_page_config(
    page_title="BERKELANA TRAVEL | Admin Loket",
    page_icon="🚐",
    layout="wide",
    initial_sidebar_state="expanded"
)

db.init_db()


def rupiah(nilai):
    return "Rp " + f"{nilai:,.0f}".replace(",", ".")


def aman(teks):
    return html.escape(str(teks))


def logo():
    lokasi = Path(__file__).resolve().parent / "logo.png"

    if lokasi.exists():
        data = base64.b64encode(lokasi.read_bytes()).decode()
        return (
            '<img src="data:image/png;base64,'
            + data
            + '" style="width:100%;max-width:175px;">'
        )

    return '<h2 style="color:#0A3967;">BERKELANA</h2>'


# ==========================================
# DESAIN
# ==========================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

.stApp {
    background: #F3F8FD;
}

.block-container {
    max-width: 1450px;
    padding-top: 2rem;
}

[data-testid="stSidebar"] {
    background: white;
    border-right: 1px solid #DCEAF6;
}

h1, h2, h3 {
    color: #0A3967 !important;
}

.stButton button[kind="primary"],
.stFormSubmitButton button[kind="primary"] {
    background: linear-gradient(120deg,#0A3967,#2479B5);
    border: none;
    border-radius: 9px;
    color: white;
    min-height: 45px;
    font-weight: 700;
}

.hero {
    background: linear-gradient(120deg,#082D54,#0A3967,#287DB9);
    border-radius: 20px;
    padding: 38px;
    color: white;
    margin-bottom: 25px;
    box-shadow: 0 12px 30px rgba(10,57,103,.13);
}

.hero h1 {
    color: white !important;
    font-size: 32px;
    margin: 10px 0;
}

.hero p {
    color: #D6EAFA;
    font-size: 14px;
}

.hero-label {
    color: #A9D6F4;
    letter-spacing: 2px;
    font-size: 12px;
    font-weight: 800;
}

.stat {
    background: white;
    border: 1px solid #E1ECF5;
    padding: 23px;
    border-radius: 15px;
    min-height: 145px;
    box-shadow: 0 5px 18px rgba(10,57,103,.04);
}

.stat-label {
    color: #71869B;
    font-size: 12px;
    font-weight: 700;
    margin-top: 10px;
}

.stat-value {
    color: #0A3967;
    font-size: 27px;
    font-weight: 800;
    margin-top: 8px;
    overflow-wrap: anywhere;
}

.section {
    background: white;
    border-left: 5px solid #5A9BD3;
    border-radius: 0 12px 12px 0;
    padding: 17px 20px;
    margin: 25px 0 18px;
}

.section h3 {
    font-size: 19px;
    margin: 0;
}

.section p {
    font-size: 13px;
    color: #71869B;
    margin: 6px 0 0;
}

.cabin {
    background: linear-gradient(90deg,#0A3967,#1E62A0);
    color: white;
    padding: 15px;
    text-align: center;
    border-radius: 10px;
    font-weight: 700;
    margin: 12px 0;
}

.driver {
    background: #E3EAF1;
    color: #52687C;
    border: 1px dashed #A7BBCD;
    border-radius: 9px;
    text-align: center;
    padding: 15px 5px;
    font-weight: 700;
}

.footer {
    text-align: center;
    color: #8CA4BA;
    font-size: 12px;
    padding: 35px 0;
}
</style>
""", unsafe_allow_html=True)


def section(judul, deskripsi=""):
    st.markdown(
        f'<div class="section"><h3>{judul}</h3>'
        f'<p>{deskripsi}</p></div>',
        unsafe_allow_html=True
    )


def stat(label, nilai, ikon):
    st.markdown(
        f'<div class="stat">'
        f'<div style="font-size:24px">{ikon}</div>'
        f'<div class="stat-label">{label}</div>'
        f'<div class="stat-value">{nilai}</div>'
        f'</div>',
        unsafe_allow_html=True
    )


def stat_row(items):
    for column, item in zip(st.columns(len(items)), items):
        with column:
            stat(*item)


def gunakan_pelanggan(id_pelanggan):
    st.session_state["menu"] = "🎫 Pemesanan Tiket"
    st.session_state["pelanggan_pemesanan"] = id_pelanggan
    st.session_state.pop("pelanggan_duplikat", None)


def tabel_transaksi(rows):
    data = [{
        "ID Order": f"BRK-{r['id_pemesanan']:05d}",
        "Pelanggan": r["nama_pelanggan"],
        "Rute": r["kota_asal"] + " → " + r["kota_tujuan"],
        "Tanggal": r["tanggal_keberangkatan"],
        "Jam": r["jam_keberangkatan"],
        "Kursi": r["kursi_dipesan"],
        "Tiket": r["jumlah_tiket"],
        "Total": rupiah(r["total_harga"])
    } for r in rows]

    st.dataframe(
        pd.DataFrame(data),
        hide_index=True,
        use_container_width=True
    )


# ==========================================
# SESSION STATE
# ==========================================

st.session_state.setdefault("kursi_pilih", [])
st.session_state.setdefault("jadwal_aktif", None)
st.session_state.setdefault("versi_form", 0)


# ==========================================
# SIDEBAR
# ==========================================

with st.sidebar:

    st.markdown(
        '<div style="text-align:center;padding:15px;">'
        + logo()
        + '<p style="color:#5A9BD3;font-size:12px;'
        'letter-spacing:1px;">YOUR JOURNEY, OUR CARE.</p>'
        '</div>',
        unsafe_allow_html=True
    )

    st.divider()
    st.caption("MENU ADMINISTRASI")

    menu = st.radio(
        "Navigasi",
        [
            "🏠 Dashboard",
            "👥 Data Pelanggan",
            "🛣️ Data Rute",
            "🎫 Pemesanan Tiket",
            "📋 Riwayat Transaksi"
        ],
        label_visibility="collapsed",
        key="menu"
    )

    st.divider()
    st.markdown("**🚐 BERKELANA TRAVEL**")
    st.caption("Sistem Administrasi Loket Kasir")
    st.caption("Homebase: Semarang")


# ==========================================
# DASHBOARD
# ==========================================

if menu == "🏠 Dashboard":

    st.markdown("""
    <div class="hero">
        <div class="hero-label">
            BERKELANA TRAVEL ADMINISTRATION SYSTEM
        </div>
        <h1>Welcome to BERKELANA TRAVEL!</h1>
        <p>Your Journey, Our Care. —
        Kelola perjalanan, pelanggan, dan transaksi
        dalam satu sistem administrasi.</p>
    </div>
    """, unsafe_allow_html=True)

    pelanggan, pesanan, rute = db.total_statistik()
    pendapatan = db.total_pendapatan()

    stat_row([
        ("TOTAL PELANGGAN", pelanggan, "👥"),
        ("RUTE AKTIF", rute, "🛣️"),
        ("TOTAL TRANSAKSI", pesanan, "🎫"),
        ("TOTAL PENDAPATAN", rupiah(pendapatan), "💰")
    ])

    section(
        "📊 Aktivitas Terbaru",
        "Lima transaksi terakhir Berkelana Travel."
    )

    rows = db.daftar_pemesanan()

    if rows:
        tabel_transaksi(rows[:5])
    else:
        st.info("Belum ada transaksi yang tercatat.")

    section("Panduan Administrasi")

    a, b, c = st.columns(3)

    with a:
        st.info(
            "**01 — Data Pelanggan**\n\n"
            "Daftarkan identitas pelanggan."
        )

    with b:
        st.info(
            "**02 — Pemesanan Tiket**\n\n"
            "Pilih rute, jadwal, dan kursi."
        )

    with c:
        st.info(
            "**03 — Riwayat Transaksi**\n\n"
            "Pantau transaksi yang tersimpan."
        )


# ==========================================
# DATA PELANGGAN
# ==========================================

elif menu == "👥 Data Pelanggan":

    st.title("👥 Data Pelanggan")
    st.caption("Pengelolaan identitas pelanggan Berkelana Travel.")
    st.divider()

    if "pesan_pelanggan" in st.session_state:
        st.success(st.session_state.pop("pesan_pelanggan"))

    section("Tambah Pelanggan Baru")

    with st.form("form_pelanggan", clear_on_submit=True):

        nama = st.text_input("Nama Lengkap *")
        telepon = st.text_input(
            "Nomor WhatsApp / Telepon *",
            placeholder="081234567890"
        )

        simpan = st.form_submit_button(
            "＋ Simpan Data Pelanggan",
            type="primary",
            use_container_width=True
        )

        if simpan:
            try:
                id_pelanggan, duplikat = db.tambah_pelanggan(nama, telepon)
                if duplikat:
                    st.session_state.pelanggan_duplikat = {
                        "id": id_pelanggan,
                        "nama": nama.strip(),
                        "telepon": telepon.strip()
                    }
                else:
                    st.session_state.pesan_pelanggan = "Data pelanggan berhasil disimpan!"
                st.rerun()

            except ValueError as e:
                st.error(str(e))

    duplikat = st.session_state.get("pelanggan_duplikat")
    if duplikat:
        st.warning(
            f"{duplikat['nama']} dengan nomor {duplikat['telepon']} "
            "sudah terdaftar. Gunakan data yang sudah ada."
        )
        st.button(
            "Gunakan untuk Pemesanan Tiket",
            on_click=gunakan_pelanggan,
            args=(duplikat["id"],),
            type="primary"
        )

    section("Daftar Pelanggan")

    rows = db.daftar_pelanggan()

    if rows:
        cari = st.text_input(
            "🔎 Cari Pelanggan",
            placeholder="Cari nama atau nomor telepon"
        )

        hasil = [
            r for r in rows
            if cari.lower() in (
                r["nama_pelanggan"] + " " + r["nomor_telepon"]
            ).lower()
        ]

        data = [{
            "Nama": r["nama_pelanggan"],
            "Telepon": r["nomor_telepon"]
        } for r in hasil]

        if data:
            st.dataframe(
                pd.DataFrame(data),
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("Pelanggan tidak ditemukan.")

    else:
        st.info("Belum ada data pelanggan.")


# ==========================================
# DATA RUTE
# ==========================================

elif menu == "🛣️ Data Rute":

    st.title("🛣️ Rute & Tarif Perjalanan")
    st.caption("Daftar rute resmi Berkelana Travel.")
    st.divider()

    st.markdown("""
    <div class="hero">
        <div class="hero-label">OUR DESTINATIONS</div>
        <h1>Explore Your Journey.</h1>
        <p>Perjalanan nyaman dari Semarang
        menuju berbagai kota tujuan.</p>
    </div>
    """, unsafe_allow_html=True)

    section("Tambah Rute")

    with st.form("form_rute", clear_on_submit=True):
        a, b, c = st.columns(3)
        asal = a.text_input("Kota Asal", value="Semarang")
        tujuan = b.text_input("Kota Tujuan")
        harga = c.number_input("Harga Tiket (Rp)", min_value=1, step=5000)
        simpan = st.form_submit_button("＋ Tambah Rute", type="primary")

    if simpan:
        try:
            db.tambah_rute(asal, tujuan, harga)
            st.success("Rute berhasil ditambahkan.")
            st.rerun()
        except ValueError as e:
            st.error(str(e))

    section("Daftar Harga Tiket", "Tarif dan status rute.")

    rute = db.daftar_rute()
    if not rute:
        st.info("Belum ada rute. Tambahkan rute melalui formulir di atas.")

    for r in rute:

        with st.container(border=True):

            a, b, c, d = st.columns(
                [2, 2, 1, 1],
                vertical_alignment="center"
            )

            with a:
                st.caption("KOTA ASAL")
                st.markdown(f"### {aman(r['kota_asal'])}")

            with b:
                st.caption("KOTA TUJUAN")
                st.markdown(f"### → {aman(r['kota_tujuan'])}")

            with c:
                st.caption("HARGA TIKET")
                st.markdown(f"**{rupiah(r['harga_tiket'])}**")

            with d:
                st.caption("STATUS")
                st.markdown("Aktif" if r["aktif"] else "Nonaktif")

    if rute:
        section("Ubah Status Rute")
        pilihan_rute = {r["id_rute"]: r for r in rute}
        id_rute_status = st.selectbox(
            "Pilih rute",
            list(pilihan_rute),
            format_func=lambda id_rute: (
                f"{pilihan_rute[id_rute]['kota_asal']} → "
                f"{pilihan_rute[id_rute]['kota_tujuan']} "
                f"({'Aktif' if pilihan_rute[id_rute]['aktif'] else 'Nonaktif'})"
            )
        )
        rute_aktif = bool(pilihan_rute[id_rute_status]["aktif"])
        if st.button("Nonaktifkan Rute" if rute_aktif else "Aktifkan Rute"):
            if db.set_status_rute(id_rute_status, not rute_aktif):
                st.success("Status rute berhasil diperbarui.")
                st.rerun()
            st.error("Rute tidak ditemukan.")


# ==========================================
# PEMESANAN TIKET
# ==========================================

elif menu == "🎫 Pemesanan Tiket":

    st.title("🎫 Pemesanan Tiket")
    st.caption("Transaksi dan pemilihan kursi penumpang.")
    st.divider()

    if "order_berhasil" in st.session_state:
        nomor = st.session_state.pop("order_berhasil")
        st.success(
            f"Transaksi BRK-{nomor:05d} berhasil disimpan!"
        )

    pelanggan = db.daftar_pelanggan()
    rute = db.daftar_rute(aktif_saja=True)

    if not pelanggan:
        st.warning(
            "Tambahkan pelanggan melalui menu Data Pelanggan "
            "terlebih dahulu."
        )

    elif not rute:
        st.warning("Data rute belum tersedia.")

    else:

        pilihan_pelanggan = {
            p["id_pelanggan"]: p for p in pelanggan
        }

        pilihan_rute = {
            r["id_rute"]: r for r in rute
        }

        section(
            "01 — Informasi Perjalanan",
            "Pilih pelanggan, rute, dan jadwal keberangkatan."
        )

        with st.container(border=True):

            a, b = st.columns(2)

            with a:

                id_pelanggan = st.selectbox(
                    "Pilih Pelanggan",
                    list(pilihan_pelanggan),
                    format_func=lambda x: (
                        pilihan_pelanggan[x]["nama_pelanggan"]
                        + " — "
                        + pilihan_pelanggan[x]["nomor_telepon"]
                    ),
                    key="pelanggan_pemesanan"
                )

                id_rute = st.selectbox(
                    "Pilih Rute",
                    list(pilihan_rute),
                    format_func=lambda x: (
                        pilihan_rute[x]["kota_asal"]
                        + " → "
                        + pilihan_rute[x]["kota_tujuan"]
                        + " | "
                        + rupiah(pilihan_rute[x]["harga_tiket"])
                    )
                )

            with b:

                tanggal = st.date_input(
                    "Tanggal Keberangkatan",
                    value=date.today(),
                    min_value=date.today(),
                    format="DD/MM/YYYY"
                )

                jam = st.selectbox(
                    "Jam Keberangkatan",
                    ["07:00", "10:00", "14:00", "16:00", "22:00"]
                )

        # ==================================
        # DENAH KURSI
        # ==================================

        section(
            "02 — Denah Kursi",
            "Kapasitas armada: 8 kursi penumpang."
        )

        jadwal_key = f"{id_rute}_{tanggal}_{jam}"

        terpesan = db.get_kursi_terpesan(
            str(tanggal), jam, id_rute
        )

        if st.session_state.jadwal_aktif != jadwal_key:
            st.session_state.jadwal_aktif = jadwal_key
            st.session_state.kursi_pilih = []
            st.session_state.versi_form += 1

        st.session_state.kursi_pilih = [
            k for k in st.session_state.kursi_pilih
            if k not in terpesan
        ]

        def tombol_kursi(nomor):

            sudah = nomor in terpesan
            dipilih = nomor in st.session_state.kursi_pilih

            if sudah:
                label = f"🔴 {nomor} · Terpesan"
            elif dipilih:
                label = f"🔵 {nomor} · Dipilih"
            else:
                label = f"💺 {nomor} · Tersedia"

            if st.button(
                label,
                key=f"seat_{jadwal_key}_{nomor}",
                disabled=sudah,
                type="primary" if dipilih else "secondary",
                use_container_width=True
            ):
                if dipilih:
                    st.session_state.kursi_pilih.remove(nomor)
                else:
                    st.session_state.kursi_pilih.append(nomor)

                # Konfirmasi pembayaran di-reset dengan
                # membuat key checkbox baru.
                st.session_state.versi_form += 1
                st.rerun()

        with st.container(border=True):
            st.markdown(
                '<div class="cabin">🚐 BAGIAN DEPAN ARMADA</div>',
                unsafe_allow_html=True
            )

            for caption, baris in (
                ("", ("K1", "SOPIR")),
                ("KABIN TENGAH — BARIS 1", ("K2", "K3")),
                ("KABIN TENGAH — BARIS 2", ("K4", "K5")),
                ("KABIN BELAKANG", ("K6", "K7", "K8")),
            ):
                if caption:
                    st.caption(caption)

                for kolom, nomor in zip(st.columns(len(baris)), baris):
                    with kolom:
                        if nomor == "SOPIR":
                            st.markdown(
                                '<div class="driver">🧑‍✈️ SOPIR / DRIVER</div>',
                                unsafe_allow_html=True
                            )
                        else:
                            tombol_kursi(nomor)

            st.divider()

            st.caption(
                f"🟢 {8 - len(set(terpesan))} kursi tersedia | "
                f"🔴 {len(set(terpesan))} kursi terpesan"
            )

        # ==================================
        # RINGKASAN PEMBAYARAN
        # ==================================

        section(
            "03 — Ringkasan Pembayaran",
            "Periksa pesanan sebelum menyimpan transaksi."
        )

        dipilih = st.session_state.kursi_pilih
        harga = pilihan_rute[id_rute]["harga_tiket"]
        jumlah = len(dipilih)
        total = jumlah * harga

        with st.container(border=True):

            a, b = st.columns(2)

            with a:
                st.caption("PELANGGAN")
                st.write(
                    pilihan_pelanggan[id_pelanggan]["nama_pelanggan"]
                )

                st.caption("KURSI DIPILIH")
                st.write(
                    ", ".join(dipilih)
                    if dipilih else "Belum memilih kursi"
                )

                st.caption("JUMLAH TIKET")
                st.write(f"{jumlah} tiket")

            with b:
                st.caption("HARGA PER TIKET")
                st.write(rupiah(harga))

                st.caption("JADWAL")
                st.write(
                    f"{tanggal.strftime('%d/%m/%Y')} — {jam} WIB"
                )

                st.caption("TOTAL PEMBAYARAN")
                st.markdown(f"## {rupiah(total)}")

            st.divider()

            # FIX ERROR CHECKBOX STREAMLIT
            # Key baru dibuat setiap formulir berubah.
            key_konfirmasi = (
                f"konfirmasi_{jadwal_key}_"
                f"{st.session_state.versi_form}"
            )

            konfirmasi = st.checkbox(
                "Pembayaran telah diterima dan "
                "data pesanan sudah sesuai.",
                key=key_konfirmasi
            )

            if st.button(
                "✓ Konfirmasi & Simpan Pemesanan",
                type="primary",
                use_container_width=True,
                disabled=(jumlah == 0 or not konfirmasi)
            ):
                try:
                    id_order = db.tambah_pemesanan(
                        id_pelanggan,
                        id_rute,
                        str(tanggal),
                        jam,
                        dipilih
                    )

                    st.session_state.kursi_pilih = []
                    st.session_state.versi_form += 1
                    st.session_state.order_berhasil = id_order

                    st.rerun()

                except ValueError as e:
                    st.error(f"Gagal menyimpan transaksi: {e}")


# ==========================================
# RIWAYAT TRANSAKSI
# ==========================================

elif menu == "📋 Riwayat Transaksi":

    st.title("📋 Riwayat Transaksi")
    st.caption("Monitoring transaksi tiket Berkelana Travel.")
    st.divider()

    if "hapus_berhasil" in st.session_state:
        nomor = st.session_state.pop("hapus_berhasil")
        st.success(
            f"Transaksi BRK-{nomor:05d} berhasil dibatalkan."
        )

    rows = db.daftar_pemesanan()

    if not rows:
        st.info("Belum ada transaksi yang tersimpan.")

    else:

        stat_row([
            ("TOTAL TRANSAKSI", len(rows), "📋"),
            ("TIKET TERJUAL", sum(r["jumlah_tiket"] for r in rows), "🎫"),
            ("TOTAL PENDAPATAN", rupiah(sum(r["total_harga"] for r in rows)), "💰")
        ])

        section("Daftar Riwayat Pemesanan")

        cari = st.text_input(
            "🔎 Cari Transaksi",
            placeholder="Cari nama atau ID transaksi"
        )

        hasil = [
            r for r in rows
            if cari.lower() in (
                r["nama_pelanggan"]
                + " "
                + str(r["id_pemesanan"])
                + " "
                + f"BRK-{r['id_pemesanan']:05d}"
            ).lower()
        ]

        if hasil:
            tabel_transaksi(hasil)
        else:
            st.info("Transaksi tidak ditemukan.")

        section("Detail Transaksi")

        pilihan_id = st.selectbox(
            "Pilih Nomor Transaksi",
            [r["id_pemesanan"] for r in rows],
            format_func=lambda x: f"BRK-{x:05d}"
        )

        transaksi = next(
            r for r in rows
            if r["id_pemesanan"] == pilihan_id
        )

        with st.container(border=True):

            st.markdown("### BERKELANA TRAVEL")
            st.caption("Your Journey, Our Care.")
            st.divider()

            for label, nilai in (
                ("Nomor Order", f"BRK-{transaksi['id_pemesanan']:05d}"),
                ("Pelanggan", aman(transaksi["nama_pelanggan"])),
                ("Nomor Telepon", aman(transaksi["nomor_telepon"])),
                ("Rute", f"{aman(transaksi['kota_asal'])} → "
                         f"{aman(transaksi['kota_tujuan'])}"),
                ("Tanggal", transaksi["tanggal_keberangkatan"]),
                ("Jam", transaksi["jam_keberangkatan"] + " WIB"),
                ("Nomor Kursi", str(transaksi["kursi_dipesan"])),
                ("Jumlah Tiket", str(transaksi["jumlah_tiket"]))
            ):
                st.write(f"**{label}:** {nilai}")

            st.divider()

            st.markdown(
                "### Total: " + rupiah(transaksi["total_harga"])
            )

        with st.expander("🗑️ Batalkan / Hapus Transaksi"):

            st.warning(
                "Pembatalan akan menghapus transaksi dan "
                "membuat kursi kembali tersedia. "
                "Pengembalian uang ditangani secara terpisah."
            )

            yakin = st.checkbox(
                "Saya yakin ingin membatalkan transaksi ini.",
                key=f"hapus_{pilihan_id}"
            )

            if st.button(
                "Hapus Transaksi Terpilih",
                disabled=not yakin,
                use_container_width=True
            ):
                berhasil = db.hapus_pemesanan(pilihan_id)

                if berhasil:
                    st.session_state.hapus_berhasil = pilihan_id
                    st.rerun()
                else:
                    st.error("Transaksi tidak ditemukan.")


# ==========================================
# FOOTER
# ==========================================

st.markdown("""
<div class="footer">
BERKELANA TRAVEL · YOUR JOURNEY, OUR CARE.<br>
Administration & Ticketing Management System © 2026
</div>
""", unsafe_allow_html=True)