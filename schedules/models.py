from django.db import models
from accounts.models import ProfilDosen
from master_data.models import Ruangan, MataKuliah, KelasAkademik
from datetime import datetime, timedelta, time

class HariLibur(models.Model):
    tanggal = models.DateField(unique=True, verbose_name="Tanggal Libur")
    keterangan = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.tanggal} - {self.keterangan}"

class SesiWaktuBase(models.Model):

    jam_mulai = models.TimeField()
    jam_selesai = models.TimeField(blank=True, null=True)

    class Meta:
        abstract = True 

    def _hitung_kalkulasi_selesai(self, sks, jam_awal):

        durasi_menit = sks * 50
        
        if isinstance(jam_awal, str):
            try:
                jam_awal = datetime.strptime(jam_awal, '%H:%M').time()
            except ValueError:
                jam_awal = datetime.strptime(jam_awal, '%H:%M:%S').time()
                
        dummy_date = datetime(2000, 1, 1, jam_awal.hour, jam_awal.minute)
        end_time = dummy_date + timedelta(minutes=durasi_menit)
        return end_time.time()

class BaseSchedule(SesiWaktuBase): 

    HARI_CHOICES = [
        (1, 'Senin'), (2, 'Selasa'), (3, 'Rabu'),
        (4, 'Kamis'), (5, 'Jumat'), (6, 'Sabtu'), (7, 'Minggu')
    ]
    
    mata_kuliah = models.ForeignKey(MataKuliah, on_delete=models.CASCADE)
    dosen_pengampu = models.ForeignKey(ProfilDosen, on_delete=models.CASCADE)
    kelas = models.ManyToManyField(KelasAkademik)
    hari = models.IntegerField(choices=HARI_CHOICES)
    ruangan_default = models.ForeignKey(Ruangan, on_delete=models.SET_NULL, null=True, blank=True)

    def clean(self):
        if self.jam_mulai and self.mata_kuliah_id:
            self.jam_selesai = self._hitung_kalkulasi_selesai(self.mata_kuliah.sks, self.jam_mulai)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"BASE: {self.mata_kuliah.kode} | {self.get_hari_display()} ({self.jam_mulai} - {self.jam_selesai})"

class ActualSession(SesiWaktuBase): 

    STATUS_CHOICES = [
        ('SCHEDULED', 'Terjadwal'),
        ('COMPLETED', 'Selesai'),
        ('CANCELED', 'Dibatalkan'),
        ('RESCHEDULED', 'Dijadwalkan Ulang')
    ]

    base_schedule = models.ForeignKey(BaseSchedule, on_delete=models.SET_NULL, null=True, blank=True, related_name='actual_sessions')
    mata_kuliah = models.ForeignKey(MataKuliah, on_delete=models.CASCADE)
    dosen_pengampu = models.ForeignKey(ProfilDosen, on_delete=models.CASCADE)
    tanggal = models.DateField()
    ruangan = models.ForeignKey(Ruangan, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='SCHEDULED')

    def clean(self):
        if self.jam_mulai and self.mata_kuliah_id:
            self.jam_selesai = self._hitung_kalkulasi_selesai(self.mata_kuliah.sks, self.jam_mulai)

    def get_projected_end_time(self, jam_mulai_baru):
  
        if not self.mata_kuliah_id:
            return None
        return self._hitung_kalkulasi_selesai(self.mata_kuliah.sks, jam_mulai_baru)

    @property
    def status_label(self):
        return dict(self.STATUS_CHOICES).get(self.status, 'Unknown')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tanggal} | {self.mata_kuliah.nama} ({self.dosen_pengampu.kode_dosen})"

class SessionKelas(models.Model):
    MODE_CHOICES = [
        ('OFFLINE', 'Offline di Ruangan'),
        ('ONLINE', 'Online / Daring'),
    ]
    
    session = models.ForeignKey(ActualSession, on_delete=models.CASCADE, related_name='peserta_kelas')
    kelas = models.ForeignKey(KelasAkademik, on_delete=models.CASCADE)
    mode = models.CharField(max_length=10, choices=MODE_CHOICES, default='OFFLINE')

    def __str__(self):
        return f"{self.kelas.nama} -> {self.session} ({self.mode})"


class PengajuanReschedule(models.Model):

    STATUS_CHOICES = [
        ('PENDING', 'Menunggu Persetujuan'),
        ('APPROVED', 'Disetujui'),
        ('REJECTED', 'Ditolak'),
    ]
    
    TIPE_CHOICES = [
        ('OFFLINE', 'Offline (Butuh Ruangan)'),
        ('ONLINE', 'Online (Tanpa Ruangan)'),
    ]

    sesi_lama = models.ForeignKey(ActualSession, on_delete=models.CASCADE, related_name='pengajuan_reschedule')
    
    tanggal_baru = models.DateField()
    jam_mulai_baru = models.TimeField()
    jam_selesai_baru = models.TimeField(blank=True, null=True) 
    
    tipe_pengganti = models.CharField(max_length=10, choices=TIPE_CHOICES, default='OFFLINE')
    ruangan_baru = models.ForeignKey(Ruangan, on_delete=models.SET_NULL, null=True, blank=True, help_text="Kosong jika Online")
    
    alasan = models.TextField(help_text="Alasan pemindahan jadwal", blank=True)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    
    catatan_admin = models.TextField(blank=True, null=True, help_text="Alasan penolakan dari Admin")
    
    dibuat_pada = models.DateTimeField(auto_now_add=True)
    diupdate_pada = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.jam_mulai_baru and self.sesi_lama:
            self.jam_selesai_baru = self.sesi_lama.get_projected_end_time(self.jam_mulai_baru)

    def __str__(self):
        return f"Reschedule {self.sesi_lama.mata_kuliah.nama} -> {self.tanggal_baru} ({self.status})"