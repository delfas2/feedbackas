from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Company(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Department(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_departments')
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_departments')

    def __str__(self):
        return f"{self.name} ({self.company.name})"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')
    
    # Naujas ryšys su Company modeliu
    company_link = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True) 
    
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    is_company_admin = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user.username} Profile'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        try:
            from PIL import Image
            img = Image.open(self.image.path)

            # Jei nuotrauka didesnė nei 300x300 pikselių, sumažiname ją
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.image.path)
        except Exception:
            pass # Jei trūksta Pillow arba paveikslėlis nerastas atmintyje (pvz., testų metu)


class ContractSettings(models.Model):
    """Sutarties nustatymai: kaina ir minimalus mokestis įmonei.
    Viena įmonė gali turėti kelias sutartis (skirtingi laikotarpiai).
    """
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name='contracts'
    )
    price_per_employee = models.DecimalField(
        max_digits=8, decimal_places=2,
        help_text="Kaina už vieną aktyvų darbuotoją per mėnesį (EUR)"
    )
    minimum_fee = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal('0.00'),
        help_text="Minimalus mėnesinis mokestis (EUR)"
    )
    contract_start = models.DateField(help_text="Sutarties pradžios data")
    contract_end = models.DateField(
        null=True, blank=True, help_text="Sutarties pabaigos data (palikite tuščią jei neterminuota)"
    )

    def __str__(self):
        return f"{self.company.name} sutarties nustatymai"

    class Meta:
        verbose_name = "Sutarties nustatymai"
        verbose_name_plural = "Sutarčių nustatymai"


class EmployeeCountLog(models.Model):
    """
    Aktyvių darbuotojų skaičiaus momentinis įrašas.
    Naujas įrašas sukuriamas kaskart, kai darbuotojas pridedamas
    arba aktyvumo statusas pasikeičia (per signalą).
    """
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name='employee_count_logs'
    )
    recorded_at = models.DateTimeField(
        default=timezone.now, help_text="Kada buvo užfiksuotas šis skaičius"
    )
    active_count = models.PositiveIntegerField(
        help_text="Aktyvių darbuotojų skaičius tuo metu"
    )

    def __str__(self):
        return f"{self.company.name} – {self.active_count} ({self.recorded_at:%Y-%m-%d %H:%M})"

    class Meta:
        ordering = ['-recorded_at']
        verbose_name = "Darbuotojų skaičiaus įrašas"
        verbose_name_plural = "Darbuotojų skaičiaus įrašai"