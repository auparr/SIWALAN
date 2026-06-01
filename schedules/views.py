from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.db.models import Q
from datetime import date, timedelta, datetime
from .models import ActualSession, PengajuanReschedule
from master_data.models import Ruangan
from django.contrib import messages
from django.http import JsonResponse

@login_required
def dashboard_dosen(request):
    hari_ini = date.today()
    
    filter_waktu = request.GET.get('filter', 'minggu_ini') 
    
    if filter_waktu == 'minggu_ini':
        batas_akhir = hari_ini + timedelta(days=7)
    elif filter_waktu == 'bulan_ini':
        batas_akhir = hari_ini + timedelta(days=30)
    else: # Jika 'semua'
        batas_akhir = None

    try:
        dosen_login = request.user.profil_dosen
        jadwal_qs = ActualSession.objects.filter(
            dosen_pengampu=dosen_login,
            tanggal__gte=hari_ini
        )
        jadwal_terdekat = ActualSession.objects.filter(dosen_pengampu=dosen_login, tanggal__gte=hari_ini).order_by('tanggal', 'jam_mulai').first()
        jadwal_akan_datang = ActualSession.objects.filter(dosen_pengampu=dosen_login, tanggal__gt=hari_ini, status__in=['SCHEDULED', 'CANCELED']).order_by('tanggal')
        jumlah_pending = PengajuanReschedule.objects.filter(
            sesi_lama__dosen_pengampu=dosen_login,
            status='PENDING'
        ).count()

    except Exception:
        dosen_login = None
        jadwal_qs = ActualSession.objects.filter(tanggal__gte=hari_ini)
        jadwal_terdekat = ActualSession.objects.filter(tanggal__gte=hari_ini).order_by('tanggal', 'jam_mulai').first()
        jadwal_akan_datang = ActualSession.objects.none()
        jumlah_pending = 0  

    if batas_akhir:
        jadwal_qs = jadwal_qs.filter(tanggal__lte=batas_akhir)

    jadwal = jadwal_qs.order_by('tanggal', 'jam_mulai')

    context = {
        'dosen': dosen_login,
        'jadwal_saya': jadwal,
        'jadwal_terdekat': jadwal_terdekat,
        'filter_aktif': filter_waktu, 
        'jadwal_akan_datang': jadwal_akan_datang,
        'jumlah_pending': jumlah_pending
    }
    return render(request, 'schedules/dashboard_dosen.html', context)

@login_required(login_url='login')
def jadwal_kampus(request):
    hari_ini = date.today()
    
    filter_waktu = request.GET.get('filter', 'hari_ini')
    search_query = request.GET.get('q', '').strip()
    
    if filter_waktu == 'hari_ini':
        jadwal_qs = ActualSession.objects.filter(tanggal=hari_ini)
    elif filter_waktu == 'besok':
        besok = hari_ini + timedelta(days=1)
        jadwal_qs = ActualSession.objects.filter(tanggal=besok)
    elif filter_waktu == 'minggu_ini':
        batas_akhir = hari_ini + timedelta(days=7)
        jadwal_qs = ActualSession.objects.filter(tanggal__gte=hari_ini, tanggal__lte=batas_akhir)
    else: 
        jadwal_qs = ActualSession.objects.filter(tanggal__gte=hari_ini)

    jadwal_qs = jadwal_qs.filter(status='SCHEDULED')
    
    if search_query:
        jadwal_qs = jadwal_qs.filter(
            Q(mata_kuliah__nama__icontains=search_query) |
            Q(ruangan__nama__icontains=search_query) |
            Q(dosen_pengampu__user__first_name__icontains=search_query) |
            Q(dosen_pengampu__user__username__icontains=search_query) |
            Q(dosen_pengampu__kode_dosen__icontains=search_query) |
            Q(dosen_pengampu__nip__icontains=search_query)
        )

    context = {
        'semua_jadwal': jadwal_qs.order_by('tanggal', 'jam_mulai'),
        'filter_aktif': filter_waktu,
        'search_query': search_query,
    }

    return render(request, 'schedules/jadwal_kampus.html', context)

@login_required(login_url='login')
def ajukan_reschedule(request):
    if request.method == "POST":
        sesi_id = request.POST.get('sesi_lama')
        tanggal_baru = request.POST.get('tanggal_baru')
        jam_mulai_baru = request.POST.get('jam_mulai_baru')
        tipe_pengganti = request.POST.get('tipe_pengganti')
        alasan = request.POST.get('alasan')
        ruangan_baru_id = request.POST.get('ruangan_baru')

        sesi_lama = ActualSession.objects.get(id=sesi_id)

        if sesi_lama.dosen_pengampu != request.user.profil_dosen:
            messages.error(request, "Anda tidak memiliki akses untuk mengajukan reschedule sesi ini.")
            return redirect('schedules:dashboard_dosen')
        
        ruang_obj = Ruangan.objects.get(id=ruangan_baru_id) if ruangan_baru_id else None

        pengajuan = PengajuanReschedule(
            sesi_lama=sesi_lama,
            tanggal_baru=tanggal_baru,
            jam_mulai_baru=jam_mulai_baru,
            tipe_pengganti=tipe_pengganti,
            alasan=alasan,
            ruangan_baru=ruang_obj
        )

        pengajuan.clean()
        pengajuan.save()

        messages.success(request, f"Berhasil! Pengajaun pemindaian jadwal {sesi_lama.mata_kuliah.nama} telah dikirim ke Admin.")

    return redirect('schedules:dashboard_dosen')

def cek_ruang_kosong(request):
    tanggal = request.GET.get('tanggal')
    jam_mulai = request.GET.get('jam_mulai')
    sesi_id = request.GET.get('sesi_id')

    if not (tanggal and jam_mulai and sesi_id):
        return JsonResponse({'ruangan': []})

    try:
        sesi = ActualSession.objects.get(id=sesi_id)
        
        durasi_menit = sesi.mata_kuliah.sks * 50
        waktu_mulai = datetime.strptime(jam_mulai, '%H:%M')
        waktu_selesai = (waktu_mulai + timedelta(minutes=durasi_menit)).time()

        jadwal_bentrok = ActualSession.objects.filter(
            tanggal=tanggal,
            status='SCHEDULED'
        ).exclude(
            jam_selesai__lte=waktu_mulai.time() 
        ).exclude(
            jam_mulai__gte=waktu_selesai      
        )

        ruang_terpakai_ids = jadwal_bentrok.values_list('ruangan_id', flat=True)

        # Hitung total mahasiswa di sesi ini
        total_mahasiswa = sum(
            sk.kelas.jumlah_mahasiswa 
            for sk in sesi.peserta_kelas.select_related('kelas')
        )

        # Filter ruangan yang kosong DAN kapasitasnya cukup
        ruang_bebas = Ruangan.objects.exclude(id__in=ruang_terpakai_ids).filter(
            kapasitas__gte=total_mahasiswa
        )


        data = [{'id': r.id, 'nama': r.nama, 'kapasitas': r.kapasitas} for r in ruang_bebas]
        return JsonResponse({'ruangan': data})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required(login_url='login')
def riwayat_reschedule(request):
    try:
        dosen_login = request.user.profil_dosen
        riwayat = PengajuanReschedule.objects.filter(
            sesi_lama__dosen_pengampu=dosen_login
        ).order_by('-dibuat_pada')
    except Exception:
        riwayat = PengajuanReschedule.objects.none()

    context = {
        'riwayat': riwayat,
    }
    return render(request, 'schedules/riwayat_reschedule.html', context)