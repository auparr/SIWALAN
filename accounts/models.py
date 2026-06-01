from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('DOSEN', 'Dosen')
    )

    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default='DOSEN')

    def __str__(self):
        return self.username

class ProfilDosen(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil_dosen')
    nip = models.CharField(max_length=25, unique=True, verbose_name='NIP')
    kode_dosen = models.CharField(max_length=15, unique=True, verbose_name="Kode Dosen")
    no_telp = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        nama_lengkap = self.user.get_full_name()

        if nama_lengkap:
            return nama_lengkap
        
        return self.user.username