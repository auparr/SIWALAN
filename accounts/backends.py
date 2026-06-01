from django.contrib.auth.backends import BaseBackend
from .models import User, ProfilDosen

class NIPBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            profil = ProfilDosen.objects.get(nip=username)
            user = profil.user

            if user.check_password(password):
                return user
            
        except ProfilDosen.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None