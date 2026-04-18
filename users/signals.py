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
    Fiksuoja aktyvių darbuotojų skaičių kaskart, kai Profile įrašomas.
    Tai apima: darbuotojo pridėjimą, perkėlimą į kitą įmonę,
    ir User.is_active pakeitimą (nes User.save() trigina Profile.save()).
    """
    from .models import EmployeeCountLog

    company = instance.company_link
    if company is None:
        return  # Profiilis be įmonės – ignoruojame

    # Skaičiuojame visus aktyvius šios įmonės darbuotojus
    active_count = Profile.objects.filter(
        company_link=company,
        user__is_active=True,
    ).count()

    EmployeeCountLog.objects.create(
        company=company,
        active_count=active_count,
    )
