from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.urls import path
from datetime import date, datetime
from .models import BaseSchedule, ActualSession, SessionKelas, PengajuanReschedule, HariLibur
from .services import approve_reschedule as service_approve, generate_semester_schedule


@admin.action(description='Approve & Pindahkan Jadwal')
def approve_reschedule_action(modeladmin, request, queryset):

    berhasil = 0
    gagal = 0

    for pengajuan in queryset:
        if pengajuan.status == 'PENDING':
            try:
                service_approve(pengajuan.id, admin_notes="Disetujui otomatis via sistem.")
                berhasil += 1
            except ValidationError as e:
                messages.error(request, f"Gagal: {pengajuan.sesi_lama.mata_kuliah.nama} — {e.messages[0]}")
                gagal += 1
            except ValueError as e:
                messages.error(request, f"Gagal: {str(e)}")
                gagal += 1
            except Exception as e:
                messages.error(request, f"Kesalahan sistem: {str(e)}")
                gagal += 1

    if berhasil > 0:
        messages.success(request, f"{berhasil} pengajuan berhasil disetujui.")

    if gagal > 0:
        messages.warning(request, f"{gagal} pengajuan gagal karena konflik.")


@admin.action(description='Tolak Pengajuan')
def reject_reschedule_action(modeladmin, request, queryset):

    updated = queryset.filter(status='PENDING').update(status='REJECTED')
    messages.warning(request, f"{updated} pengajuan telah ditolak.")

class SessionKelasInline(admin.TabularInline):

    model = SessionKelas
    extra = 0
    fields = ('kelas', 'mode')

    def get_extra(self, request, obj=None, **kwargs):
        return 0 if obj is None else 1

    def has_add_permission(self, request, obj=None):
        return obj is not None


@admin.register(BaseSchedule)
class BaseScheduleAdmin(admin.ModelAdmin):

    list_display = ('mata_kuliah', 'dosen_pengampu', 'hari_label', 'jam_mulai', 'jam_selesai', 'ruangan_default', 'jumlah_kelas')
    list_filter = ('hari', 'dosen_pengampu', 'ruangan_default')
    search_fields = ('mata_kuliah__nama', 'mata_kuliah__kode', 'dosen_pengampu__user__first_name')
    filter_horizontal = ('kelas',)

    @admin.display(description='Hari')
    def hari_label(self, obj):
        return obj.get_hari_display()

    @admin.display(description='Jumlah Kelas')
    def jumlah_kelas(self, obj):
        return obj.kelas.count()

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('generate-semester/', self.admin_site.admin_view(self.generate_semester_view), name='generate_semester'),
        ]
        return custom + urls

    def generate_semester_view(self, request):

        context = {
            'title': 'Generate Jadwal Semester',
            'opts': self.model._meta,
            'hasil': None,
            'error_logs': [],
        }

        if request.method == 'POST':
            tanggal_str = request.POST.get('tanggal_mulai')
            jumlah_minggu_str = request.POST.get('jumlah_minggu', '16')

            if not tanggal_str:
                messages.error(request, "Tanggal mulai semester wajib diisi.")
                return render(request, 'admin/schedules/generate_semester.html', context)

            try:
                tanggal_mulai = datetime.strptime(tanggal_str, '%Y-%m-%d').date()
                jumlah_minggu = int(jumlah_minggu_str)

                if jumlah_minggu < 1 or jumlah_minggu > 52:
                    raise ValueError("Jumlah minggu harus antara 1 dan 52.")

                if tanggal_mulai < date.today():
                    messages.warning(request, "Peringatan: Tanggal mulai semester sudah lewat.")

            except ValueError as e:
                messages.error(request, f"Input tidak valid: {str(e)}")
                return render(request, 'admin/schedules/generate_semester.html', context)

            try:
                sesi_terbuat, error_logs = generate_semester_schedule(tanggal_mulai, jumlah_minggu)
                context['hasil'] = sesi_terbuat
                context['error_logs'] = error_logs

                if sesi_terbuat > 0:
                    messages.success(request, f"Berhasil membuat {sesi_terbuat} sesi kuliah untuk {jumlah_minggu} minggu.")
                if error_logs:
                    messages.warning(request, f"{len(error_logs)} sesi dilewati karena konflik. Lihat detail di bawah.")

            except Exception as e:
                messages.error(request, f"Terjadi kesalahan saat generate: {str(e)}")

        return render(request, 'admin/schedules/generate_semester.html', context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['generate_semester_url'] = 'generate-semester/'
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(ActualSession)
class ActualSessionAdmin(admin.ModelAdmin):

    list_display = ('tanggal', 'mata_kuliah', 'dosen_pengampu', 'jam_mulai', 'jam_selesai', 'ruangan', 'status', 'jumlah_peserta')
    list_filter = ('status', 'dosen_pengampu', 'ruangan', 'tanggal')
    search_fields = ('mata_kuliah__nama', 'mata_kuliah__kode', 'dosen_pengampu__user__first_name')
    date_hierarchy = 'tanggal'
    inlines = [SessionKelasInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    def get_readonly_fields(self, request, obj=None):
        if obj: 
            return ('mata_kuliah', 'dosen_pengampu', 'tanggal', 'jam_mulai', 'jam_selesai', 'ruangan', 'base_schedule')
        return ()

    @admin.display(description='Total Peserta Offline')
    def jumlah_peserta(self, obj):
        total = sum(
            sk.kelas.jumlah_mahasiswa
            for sk in obj.peserta_kelas.filter(mode='OFFLINE').select_related('kelas')
        )
        return total if total else '—'
@admin.register(PengajuanReschedule)
class PengajuanRescheduleAdmin(admin.ModelAdmin):
    list_display = ('mata_kuliah_label', 'dosen_label', 'jadwal_lama', 'jadwal_baru', 'tipe_pengganti', 'status', 'dibuat_pada')
    list_filter = ('status', 'tipe_pengganti', 'dibuat_pada')
    search_fields = ('sesi_lama__mata_kuliah__nama', 'sesi_lama__dosen_pengampu__user__first_name')
    readonly_fields = ('dibuat_pada', 'diupdate_pada', 'jam_selesai_baru')
    actions = [approve_reschedule_action, reject_reschedule_action]

    fieldsets = (
        ('Sesi Yang Dipindahkan', {
            'fields': ('sesi_lama',)
        }),
        ('Jadwal Baru', {
            'fields': ('tanggal_baru', 'jam_mulai_baru', 'jam_selesai_baru', 'tipe_pengganti', 'ruangan_baru')
        }),
        ('Keterangan', {
            'fields': ('alasan', 'status', 'catatan_admin')
        }),
        ('Timestamp', {
            'fields': ('dibuat_pada', 'diupdate_pada'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Mata Kuliah')
    def mata_kuliah_label(self, obj):
        return obj.sesi_lama.mata_kuliah.nama

    @admin.display(description='Dosen')
    def dosen_label(self, obj):
        return obj.sesi_lama.dosen_pengampu.user.get_full_name()

    @admin.display(description='Jadwal Lama')
    def jadwal_lama(self, obj):
        return f"{obj.sesi_lama.tanggal} {obj.sesi_lama.jam_mulai}"

    @admin.display(description='Jadwal Baru')
    def jadwal_baru(self, obj):
        return f"{obj.tanggal_baru} {obj.jam_mulai_baru}"

@admin.register(HariLibur)
class HariLiburAdmin(admin.ModelAdmin):
    list_display = ('tanggal', 'keterangan')
    search_fields = ('keterangan',)
    date_hierarchy = 'tanggal'