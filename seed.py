import os
import django
from datetime import date, time, timedelta

from accounts.models import User, ProfilDosen
from schedules.models import Ruangan, MataKuliah, KelasAkademik, BaseSchedule, HariLibur

def run_seeder():
    print("Mulai mengisi data dummy (Versi Ramai) untuk Demo UNESA...")

    # 1. RUANGAN (Ada yang besar, ada yang kecil untuk jebakan)
    r1, _ = Ruangan.objects.get_or_create(nama="Lab Komputer 1", defaults={'kapasitas': 40})
    r2, _ = Ruangan.objects.get_or_create(nama="Ruang Teori A", defaults={'kapasitas': 20}) # Jebakan
    r3, _ = Ruangan.objects.get_or_create(nama="Auditorium", defaults={'kapasitas': 100})
    r4, _ = Ruangan.objects.get_or_create(nama="Ruang Teori B", defaults={'kapasitas': 35})
    r5, _ = Ruangan.objects.get_or_create(nama="Lab Jaringan", defaults={'kapasitas': 30})
    print("✅ 5 Ruangan berhasil dibuat.")

    # 2. DOSEN
    user_dosen1, _ = User.objects.get_or_create(username="adit_dosen", defaults={'first_name': 'Adit', 'role': 'DOSEN'})
    user_dosen1.set_password('dosen123')
    user_dosen1.save()
    dosen1, _ = ProfilDosen.objects.get_or_create(user=user_dosen1, defaults={'nip': '19800101', 'kode_dosen': 'ADT', 'no_telp': '081111'})

    user_dosen2, _ = User.objects.get_or_create(username="susi_dosen", defaults={'first_name': 'Susi', 'role': 'DOSEN'})
    user_dosen2.set_password('dosen123')
    user_dosen2.save()
    dosen2, _ = ProfilDosen.objects.get_or_create(user=user_dosen2, defaults={'nip': '19800202', 'kode_dosen': 'SSI', 'no_telp': '082222'})

    user_dosen3, _ = User.objects.get_or_create(username="budi_dosen", defaults={'first_name': 'Budi', 'role': 'DOSEN'})
    user_dosen3.set_password('dosen123')
    user_dosen3.save()
    dosen3, _ = ProfilDosen.objects.get_or_create(user=user_dosen3, defaults={'nip': '19800303', 'kode_dosen': 'BDI', 'no_telp': '083333'})
    print("✅ 3 Dosen berhasil dibuat (Password: dosen123).")

    # 3. KELAS AKADEMIK (Sudah ada angkatan!)
    k1, _ = KelasAkademik.objects.get_or_create(nama="TI-A 2025", defaults={'jumlah_mahasiswa': 30, 'angkatan': 2025})
    k2, _ = KelasAkademik.objects.get_or_create(nama="TI-B 2025", defaults={'jumlah_mahasiswa': 35, 'angkatan': 2025})
    k3, _ = KelasAkademik.objects.get_or_create(nama="TI-C 2025", defaults={'jumlah_mahasiswa': 25, 'angkatan': 2025})
    print("✅ 3 Kelas berhasil dibuat.")

    # 4. MATA KULIAH
    mk1, _ = MataKuliah.objects.get_or_create(kode="TIF101", defaults={'nama': 'Pemrograman Web', 'sks': 3})
    mk2, _ = MataKuliah.objects.get_or_create(kode="TIF102", defaults={'nama': 'Kecerdasan Buatan', 'sks': 2})
    mk3, _ = MataKuliah.objects.get_or_create(kode="TIF103", defaults={'nama': 'Basis Data', 'sks': 3})
    mk4, _ = MataKuliah.objects.get_or_create(kode="TIF104", defaults={'nama': 'Jaringan Komputer', 'sks': 2})
    print("✅ 4 Mata Kuliah berhasil dibuat.")

    # 5. HARI LIBUR
    besok = date.today() + timedelta(days=6)
    HariLibur.objects.get_or_create(tanggal=besok, defaults={'keterangan': 'Cuti Bersama Demo Aplikasi'})
    print("✅ 1 Hari Libur (Besok) disiapkan.")

    # 6. BASE SCHEDULE (Disebar ke hari Senin, Selasa, Rabu agar kalender penuh)
    # Jadwal Adit (Senin)
    bs1, c1 = BaseSchedule.objects.get_or_create(
        mata_kuliah=mk1, dosen_pengampu=dosen1, hari=1, defaults={'jam_mulai': time(8, 0), 'ruangan_default': r1}
    )
    if c1: bs1.kelas.add(k1)

    # Jadwal susi (Senin) -> Jebakan Kapasitas!
    bs2, c2 = BaseSchedule.objects.get_or_create(
        mata_kuliah=mk2, dosen_pengampu=dosen2, hari=1, defaults={'jam_mulai': time(10, 0), 'ruangan_default': r2}
    )
    if c2: bs2.kelas.add(k1, k2) # Gabungan 65 mahasiswa di ruang kapasitas 20

    # Jadwal Budi (Selasa)
    bs3, c3 = BaseSchedule.objects.get_or_create(
        mata_kuliah=mk3, dosen_pengampu=dosen3, hari=2, defaults={'jam_mulai': time(13, 0), 'ruangan_default': r3}
    )
    if c3: bs3.kelas.add(k1, k2, k3)

    # Jadwal Adit (Rabu) - Biar Adit punya banyak jadwal di dashboard
    bs4, c4 = BaseSchedule.objects.get_or_create(
        mata_kuliah=mk4, dosen_pengampu=dosen1, hari=3, defaults={'jam_mulai': time(9, 0), 'ruangan_default': r5}
    )
    if c4: bs4.kelas.add(k3)

    print("✅ Base Schedule berhasil dibuat.")
    print("🎉 Data Dummy Ekstra Ramai SIAP! ")

run_seeder()