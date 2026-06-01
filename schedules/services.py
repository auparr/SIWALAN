from datetime import timedelta, datetime
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import BaseSchedule, ActualSession, SessionKelas, HariLibur, PengajuanReschedule

def _hitung_jam_selesai(jam_mulai, sks):
    durasi_menit = sks * 50
    dummy = datetime(2000, 1, 1, jam_mulai.hour, jam_mulai.minute)
    return (dummy + timedelta(minutes=durasi_menit)).time()

def validate_full_session(tanggal, jam_mulai, jam_selesai, dosen_pengampu, ruangan=None, kelas_offline_list=None, kelas_online_list=None, exclude_session_id=None):
    """
    Mesin Validasi Utama Skala Enterprise.
    Menyapu bersih semua kemungkinan bentrok (Holiday, Capacity, Collision).
    """
    kelas_offline_list = kelas_offline_list or []
    kelas_online_list = kelas_online_list or []
    semua_kelas = kelas_offline_list + kelas_online_list

    libur = HariLibur.objects.filter(tanggal=tanggal).first()
    if libur:
        raise ValidationError(f"Gagal: Tanggal {tanggal} adalah hari libur ({libur.keterangan}).")

    if ruangan and kelas_offline_list:
        total_peserta_offline = sum(kelas.jumlah_mahasiswa for kelas in kelas_offline_list)
        if total_peserta_offline > ruangan.kapasitas:
            raise ValidationError(
                f"Kapasitas ruangan {ruangan.nama} tidak mencukupi! "
                f"Kapasitas Maksimal: {ruangan.kapasitas}, Total Hadir Fisik: {total_peserta_offline}."
            )

    overlap_sessions = ActualSession.objects.filter(
        tanggal=tanggal,
        jam_mulai__lt=jam_selesai,
        jam_selesai__gt=jam_mulai
    ).exclude(status='CANCELED')

    if exclude_session_id:
        overlap_sessions = overlap_sessions.exclude(id=exclude_session_id)

    if not overlap_sessions.exists():
        return True 

    if overlap_sessions.filter(dosen_pengampu=dosen_pengampu).exists():
        raise ValidationError(f"Bentrok Dosen: {dosen_pengampu.user.first_name} sudah mengajar di kelas lain pada jam ini.")

    if ruangan:
        if overlap_sessions.filter(ruangan=ruangan).exists():
            raise ValidationError(f"Bentrok Ruangan: {ruangan.nama} sedang dipakai oleh jadwal lain.")

    if semua_kelas:
        kelas_ids = [k.id for k in semua_kelas]
        
        bentrok_kelas = SessionKelas.objects.filter(
            session__in=overlap_sessions,
            kelas_id__in=kelas_ids
        )
        if bentrok_kelas.exists():
            nama_kelas = ", ".join(set([bk.kelas.nama for bk in bentrok_kelas]))
            raise ValidationError(f"Bentrok Kelas: Mahasiswa kelas {nama_kelas} sudah ada jadwal perkuliahan lain.")

    return True

@transaction.atomic
def generate_semester_schedule(tanggal_mulai_semester, jumlah_minggu=16):
    """
    Mesin Pencetak Jadwal 1 Semester.
    Membaca BaseSchedule dan mencetak ActualSession untuk 16 minggu.
    """
    base_schedules = BaseSchedule.objects.all()
    tanggal_akhir_semester = tanggal_mulai_semester + timedelta(weeks=jumlah_minggu)
    
    sesi_terbuat = 0
    error_logs = []

    for base in base_schedules:
        target_weekday = base.hari - 1 
        
        days_ahead = target_weekday - tanggal_mulai_semester.weekday()
        if days_ahead < 0:
            days_ahead += 7 
        
        tanggal_kuliah = tanggal_mulai_semester + timedelta(days=days_ahead)
        
        while tanggal_kuliah < tanggal_akhir_semester:
            status_sesi = 'SCHEDULED'
            ruangan_sesi = base.ruangan_default
            
            kelas_list = list(base.kelas.all())

            libur = HariLibur.objects.filter(tanggal=tanggal_kuliah).first()
            if libur:
                status_sesi = 'CANCELED'
                ruangan_sesi = None 
            
            if status_sesi == 'SCHEDULED':

                jam_selesai_aktual = _hitung_jam_selesai(base.jam_mulai, base.mata_kuliah.sks)
                try:
                    validate_full_session(
                        tanggal=tanggal_kuliah,
                        jam_mulai=base.jam_mulai,
                        jam_selesai=jam_selesai_aktual,  
                        dosen_pengampu=base.dosen_pengampu,
                        ruangan=ruangan_sesi,
                        kelas_offline_list=kelas_list
                    )
                except ValidationError as e:
                    pesan_error = f"GAGAL: {base.mata_kuliah.kode} tgl {tanggal_kuliah.strftime('%d-%m-%Y')} - {e.messages[0]}"
                    error_logs.append(pesan_error)
                    tanggal_kuliah += timedelta(weeks=1)
                    continue 

            new_session = ActualSession(
                base_schedule=base,
                mata_kuliah=base.mata_kuliah,
                dosen_pengampu=base.dosen_pengampu,
                tanggal=tanggal_kuliah,
                jam_mulai=base.jam_mulai,
                ruangan=ruangan_sesi,
                status=status_sesi
            )
            new_session.save() 
            
            for kelas_akademik in kelas_list:
                SessionKelas.objects.create(
                    session=new_session,
                    kelas=kelas_akademik,
                    mode='OFFLINE' if status_sesi == 'SCHEDULED' else 'ONLINE'
                )
            
            sesi_terbuat += 1
            
            tanggal_kuliah += timedelta(weeks=1)

    return sesi_terbuat, error_logs


@transaction.atomic
def approve_reschedule(reschedule_id, admin_notes=""):

    req = PengajuanReschedule.objects.select_for_update().get(id=reschedule_id)
    sesi_lama = req.sesi_lama
    
    if req.status != 'PENDING':
        raise ValueError("Hanya pengajuan berstatus PENDING yang bisa diproses.")

    pivot_kelas_lama = SessionKelas.objects.filter(session=sesi_lama)
    kelas_offline = []
    kelas_online = []
    mode_baru = req.tipe_pengganti
    
    for pk in pivot_kelas_lama:
        if mode_baru == 'OFFLINE':
            kelas_offline.append(pk.kelas)
        else:
            kelas_online.append(pk.kelas)

    validate_full_session(
        tanggal=req.tanggal_baru,
        jam_mulai=req.jam_mulai_baru,
        jam_selesai=req.jam_selesai_baru,
        dosen_pengampu=sesi_lama.dosen_pengampu, 
        ruangan=req.ruangan_baru if mode_baru == 'OFFLINE' else None, 
        kelas_offline_list=kelas_offline,
        kelas_online_list=kelas_online,
        exclude_session_id=sesi_lama.id 
    )

    if sesi_lama.status == 'SCHEDULED':
        sesi_lama.status = 'RESCHEDULED'
        sesi_lama.save()

    sesi_baru = ActualSession.objects.create(
        base_schedule=sesi_lama.base_schedule,
        mata_kuliah=sesi_lama.mata_kuliah,
        dosen_pengampu=sesi_lama.dosen_pengampu,
        tanggal=req.tanggal_baru,
        jam_mulai=req.jam_mulai_baru,
        jam_selesai=req.jam_selesai_baru,
        ruangan=req.ruangan_baru if mode_baru == 'OFFLINE' else None,
        status='SCHEDULED'
    )

    sesi_kelas_baru_bulk = []
    for pk in pivot_kelas_lama:
        sesi_kelas_baru_bulk.append(
            SessionKelas(
                session=sesi_baru,
                kelas=pk.kelas,
                mode=mode_baru
            )
        )
    SessionKelas.objects.bulk_create(sesi_kelas_baru_bulk) 

    req.status = 'APPROVED'
    req.catatan_admin = admin_notes
    req.save()

    return True