from django.urls import path
from . import views

app_name = 'schedules'

urlpatterns = [
    path('dashboard/', views.dashboard_dosen, name='dashboard_dosen'),
    path('jadwal-kampus/', views.jadwal_kampus, name='jadwal_kampus'),
    path('ajukan-reschedule/', views.ajukan_reschedule, name='ajukan_reschedule'),
    path('api/cek-ruang/', views.cek_ruang_kosong, name="api_cek_ruang"),
    path('riwayat-reschedule/', views.riwayat_reschedule, name='riwayat_reschedule')
]