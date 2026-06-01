from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ProfilDosen

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')

    fieldsets = UserAdmin.fieldsets + (('Informasi Tambahan', {'fields': ('role',)}),)

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informasi Tambahan', {'fields': ('role',)}),
    )

@admin.register(ProfilDosen)
class ProfilDosenAdmin(admin.ModelAdmin):
    list_display = ('user', 'nip', 'kode_dosen', 'no_telp')
    search_fields = ('user__username', 'nip')