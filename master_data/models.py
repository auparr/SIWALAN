from django.db import models

# Create your models here.
class Ruangan(models.Model):
    nama = models.CharField(max_length=50, unique=True, verbose_name="Nama Ruangan")
    kapasitas = models.IntegerField(verbose_name="Kapasitas Maksimal (Orang)")
    is_hybrid = models.BooleanField(default=False, verbose_name="Fasilitas Hybrid (Kamera/Proyektor)")
    is_active = models.BooleanField(default=True, verbose_name="Status Aktif")

    def __str__(self):
        return f"{self.nama} (Kap: {self.kapasitas})"


class MataKuliah(models.Model):
    kode = models.CharField(max_length=20, unique=True, verbose_name="Kode Matkul")
    nama = models.CharField(max_length=100, verbose_name="Nama Mata Kuliah")
    sks = models.IntegerField(verbose_name="Bobot SKS")

    def __str__(self):
        return f"{self.kode} - {self.nama}"


class KelasAkademik(models.Model):
    nama = models.CharField(max_length=50, unique=True, verbose_name="Nama Kelas")
    program_studi = models.CharField(max_length=100)
    angkatan = models.IntegerField()
    jumlah_mahasiswa = models.IntegerField(default=0, verbose_name="Estimasi Jumlah Mahasiswa")

    def __str__(self):
        return self.nama