from decimal import Decimal
from datetime import date
from django.utils import timezone
from django.db.models import Q


def calculate_monthly_bill(company_id: int, year: int, month: int) -> dict:
    """
    Apskaičiuoja mėnesio sąskaitą konkrečiai įmonei.

    Algoritmas:
    1. Suranda sutartį, galiojusią tą mėnesį (contract_start ≤ mėnuo ≤ contract_end).
    2. Suranda visus EmployeeCountLog įrašus tame mėnesyje.
    3. Išrenka didžiausią active_count (Max Count).
    4. Jei mėnesiui įrašų nėra – paimamas paskutinis žinomas skaičius.
    5. suma = max(max_count * price_per_employee, minimum_fee)

    Grąžina dict su visais skaičiavimo detaliais.
    """
    from .models import Company, ContractSettings, EmployeeCountLog, Profile

    try:
        company = Company.objects.get(pk=company_id)
    except Company.DoesNotExist:
        return {'error': f'Įmonė su ID {company_id} nerasta.'}

    # Mėnesio ribos
    month_start = date(year, month, 1)
    if month == 12:
        month_end = date(year + 1, 1, 1)
    else:
        month_end = date(year, month + 1, 1)

    # Sutartis, galiojusi tą mėnesį (persidengia su mėnesiu):
    # contract_start < month_end IR (contract_end nėra ARBA contract_end >= month_start)
    settings = (
        ContractSettings.objects
        .filter(company=company, contract_start__lt=month_end)
        .filter(Q(contract_end__isnull=True) | Q(contract_end__gte=month_start))
        .order_by('-contract_start')
        .first()
    )

    if settings is None:
        return {
            'company': company,
            'error': 'Šiam mėnesiui galiojančios sutarties nerasta.',
            'has_settings': False,
        }


    # Logai tame mėnesyje
    logs_this_month = EmployeeCountLog.objects.filter(
        company=company,
        recorded_at__date__gte=month_start,
        recorded_at__date__lt=month_end,
    ).order_by('-active_count')

    if logs_this_month.exists():
        max_count = logs_this_month.first().active_count
        data_source = 'Logai iš pasirinkto mėnesio'
    else:
        # Nėra logų tame mėnesyje – paimame paskutinį prieš mėnesio pradžią
        last_before = EmployeeCountLog.objects.filter(
            company=company,
            recorded_at__date__lt=month_start,
        ).order_by('-recorded_at').first()

        if last_before:
            max_count = last_before.active_count
            data_source = f'Paskutinis žinomas skaičius ({last_before.recorded_at:%Y-%m-%d})'
        else:
            # Visai nėra logų – skaičiuojame dabartinį aktyvų skaičių
            max_count = Profile.objects.filter(company_link=company, user__is_active=True).count()
            data_source = 'Dabartinis skaičius (nėra istorinių logų)'

    price = settings.price_per_employee
    raw_amount = Decimal(max_count) * price
    final_amount = max(raw_amount, settings.minimum_fee)

    return {
        'company': company,
        'has_settings': True,
        'settings': settings,
        'year': year,
        'month': month,
        'month_label': date(year, month, 1).strftime('%Y %B'),
        'max_count': max_count,
        'data_source': data_source,
        'price_per_employee': price,
        'raw_amount': raw_amount,
        'minimum_fee': settings.minimum_fee,
        'final_amount': final_amount,
        'minimum_applied': final_amount > raw_amount,
        'contract_start': settings.contract_start,
        'contract_end': settings.contract_end,
        'logs_count': logs_this_month.count(),
    }
