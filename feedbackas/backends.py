from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        # Naudojame filter vietoj get, kad išvengtume klaidų, jei yra keli vartotojai su tuo pačiu el. paštu
        users = UserModel.objects.filter(email=username)
        for user in users:
            if user.check_password(password):
                return user
        return None
