import logging
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import redirect
from users.models import Profile, Company

logger = logging.getLogger(__name__)


class MicrosoftSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter for Microsoft Entra ID social login.
    Automatiškai sukuria Profile ir priskiria Company pagal el. pašto domeną.
    """

    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        """Logavimas klaidos atveju – padeda debuginti 'Third-Party Login Failure'."""
        logger.error(
            f"Microsoft SSO klaida: provider={provider_id}, error={error}, "
            f"exception={exception}, extra_context={extra_context}"
        )
        return super().authentication_error(request, provider_id, error, exception, extra_context)

    def pre_social_login(self, request, sociallogin):
        """
        Automatiškai susieja Microsoft paskyrą su esamu vartotoju,
        jei el. pašto adresas sutampa.
        Blokuoja prisijungimą, jei domenas nesusietas su jokia įmone.
        """
        # Jei jau susieta – nieko nedaryti
        if sociallogin.is_existing:
            return

        # Gauti el. paštą iš socialinio prisijungimo
        email = None
        if sociallogin.email_addresses:
            email = sociallogin.email_addresses[0].email
        if not email:
            extra_data = sociallogin.account.extra_data or {}
            email = extra_data.get('mail') or extra_data.get('userPrincipalName', '')

        if not email:
            return

        # Ieškoti esamo vartotojo su tuo pačiu el. paštu
        try:
            existing_user = User.objects.get(email__iexact=email)
            # Jei tai superuser – visada leisti
            if existing_user.is_superuser:
                sociallogin.connect(request, existing_user)
                return
            # Susieti Microsoft paskyrą su esamu vartotoju
            sociallogin.connect(request, existing_user)
            logger.info(f"Microsoft paskyra automatiškai susieta su esamu vartotoju: {email}")
            return
        except User.DoesNotExist:
            pass  # Naujas vartotojas – tikrinsime domeną
        except User.MultipleObjectsReturned:
            # Jei keli vartotojai su tuo pačiu el. paštu – imti pirmą aktyvų
            existing_user = User.objects.filter(email__iexact=email, is_active=True).first()
            if existing_user:
                sociallogin.connect(request, existing_user)
                logger.info(f"Microsoft paskyra susieta su esamu vartotoju (multi): {email}")
                return

        # Naujas vartotojas – tikrinti ar domenas susietas su įmone
        company = self._find_company_by_email(email)
        if not company:
            logger.warning(f"Microsoft SSO atmestas – domenas nesusietas su įmone: {email}")
            messages.error(request, "Jūsų įmonė sistemoje neužregistruota. Susisiekite su administratoriumi.")
            raise ImmediateHttpResponse(redirect('login'))

    def save_user(self, request, sociallogin, form=None):
        """Iškviečiamas kai naujas vartotojas registruojasi per socialinį tiekėją."""
        user = super().save_user(request, sociallogin, form)

        # Užpildyti vardą/pavardę iš Microsoft profilio, jei trūksta
        extra_data = sociallogin.account.extra_data or {}
        if not user.first_name and extra_data.get('givenName'):
            user.first_name = extra_data['givenName']
        if not user.last_name and extra_data.get('surname'):
            user.last_name = extra_data['surname']
        if user.first_name or user.last_name:
            user.save(update_fields=['first_name', 'last_name'])

        # Priskirti Company pagal el. pašto domeną
        # Profile jau gali būti sukurtas per User post_save signalą
        company = self._find_company_by_email(user.email)
        try:
            profile = user.profile
            if not profile.company_link and company:
                profile.company_link = company
                profile.save(update_fields=['company_link'])
                logger.info(
                    f"Microsoft vartotojas {user.email} priskirtas įmonei '{company.name}'"
                )
        except Profile.DoesNotExist:
            Profile.objects.create(user=user, company_link=company)
            if company:
                logger.info(
                    f"Naujas Microsoft vartotojas {user.email} priskirtas įmonei '{company.name}'"
                )
            else:
                logger.info(
                    f"Naujas Microsoft vartotojas {user.email} – atitinkamos įmonės nerasta"
                )

        return user

    def _find_company_by_email(self, email):
        """
        Ieško Company pagal el. pašto domeną.
        1. Pirmiausia tikrina ar yra Company su atitinkamu email_domain lauku.
        2. Jei nerasta – bando rasti pagal esamų vartotojų el. pašto domeną (fallback).
        """
        if not email or '@' not in email:
            return None

        domain = email.split('@')[1].lower()

        # 1. Tikrinti pagal Company.email_domain lauką
        company_by_domain = Company.objects.filter(
            email_domain__iexact=domain,
            is_active=True,
        ).first()

        if company_by_domain:
            return company_by_domain

        # 2. Fallback: rasti profilį su tuo pačiu domenu ir priskirta įmone
        matching_profile = (
            Profile.objects
            .filter(
                user__email__iendswith=f'@{domain}',
                company_link__isnull=False,
                company_link__is_active=True,
            )
            .select_related('company_link')
            .first()
        )

        if matching_profile:
            return matching_profile.company_link

        return None
