from django.contrib import admin
from .models import Ruangan, MataKuliah, KelasAkademik

@admin.register(Ruangan)
class RuanganAdmin(admin.ModelAdmin):
    list_display = ('nama', 'kapasitas', 'is_hybrid', 'is_active')
    list_filter = ('is_hybrid', 'is_active')
    search_fields = ('nama',)

@admin.register(MataKuliah)
class MataKuliahAdmin(admin.ModelAdmin):
    list_display = ('kode', 'nama', 'sks')
    list_filter = ('sks',)
    search_fields = ('kode', 'nama')

@admin.register(KelasAkademik)
class KelasAkademikAdmin(admin.ModelAdmin):
    list_display = ('nama', 'program_studi', 'angkatan', 'jumlah_mahasiswa')
    list_filter = ('program_studi', 'angkatan')
    search_fields = ('nama', 'program_studi')