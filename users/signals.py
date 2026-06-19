from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=Profile)
def log_employee_count_on_profile_save(sender, instance, **kwargs):
    """
    Fiksuoja aktyvių darbuotojų skaičių kartą per dieną kiekvienai įmonei.
    Jei šiandien jau yra įrašas – atnaujina jo skaičių.
    Jei dar nėra – sukuria naują.
    """
    from django.utils import timezone
    from .models import EmployeeCountLog

    company = instance.company_link
    if company is None:
        return  # Profilis be įmonės – ignoruojame

    today = timezone.now().date()

    # Skaičiuojame visus aktyvius šios įmonės darbuotojus
    active_count = Profile.objects.filter(
        company_link=company,
        user__is_active=True,
    ).count()

    # Vienas įrašas per dieną – atnaujina arba sukuria
    EmployeeCountLog.objects.update_or_create(
        company=company,
        recorded_at__date=today,
        defaults={
            'active_count': active_count,
            'recorded_at': timezone.now(),
        },
    )
