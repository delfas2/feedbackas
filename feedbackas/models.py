from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class FeedbackRequest(models.Model):
    requester = models.ForeignKey(User, related_name='made_requests', on_delete=models.CASCADE)
    requested_to = models.ForeignKey(User, related_name='received_requests', on_delete=models.CASCADE)
    project_name = models.CharField(max_length=255)
    questionnaire = models.ForeignKey('Questionnaire', on_delete=models.SET_NULL, null=True, blank=True, related_name='feedback_requests')
    comment = models.TextField(blank=True, null=True)
    due_date = models.DateField()
    status = models.CharField(max_length=20, default='pending')
    is_self_initiated = models.BooleanField(default=False, help_text='True jei atsiliepimas inicijuotas paties vertintojo, o ne paprašytas')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Feedback request from {self.requester} to {self.requested_to} for {self.project_name}"

class Feedback(models.Model):
    feedback_request = models.OneToOneField(FeedbackRequest, on_delete=models.CASCADE)
    rating = models.IntegerField(help_text="Bendras įvertinimas")
    # Pridėkite trūkstamus laukus:
    teamwork_rating = models.IntegerField(default=5)
    communication_rating = models.IntegerField(default=5)
    initiative_rating = models.IntegerField(default=5)
    technical_skills_rating = models.IntegerField(default=5)
    problem_solving_rating = models.IntegerField(default=5)

    keywords = models.CharField(max_length=255)
    comments = models.TextField(blank=True)
    feedback = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    # AI išskirtos savybės iš atsiliepimo ir komentaro
    extracted_strengths = models.JSONField(default=list, blank=True)
    extracted_improvements = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"Feedback for {self.feedback_request}"

class Trait(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_traits')

    def __str__(self):
        return self.name

class Questionnaire(models.Model):
    title = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questionnaires')
    traits = models.ManyToManyField(Trait, blank=True, related_name='questionnaires')
    is_team = models.BooleanField(default=False)
    target_department = models.ForeignKey('users.Department', null=True, blank=True, on_delete=models.SET_NULL, related_name='team_questionnaires')
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

class TraitRating(models.Model):
    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE, related_name='trait_ratings')
    trait = models.ForeignKey(Trait, on_delete=models.CASCADE)
    rating = models.IntegerField(default=0)

    class Meta:
        unique_together = ('feedback', 'trait')

    def __str__(self):
        return f"{self.trait.name}: {self.rating} (Feedback #{self.feedback.id})"

class AIUsageLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_usage_logs')
    company = models.ForeignKey('users.Company', on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_usage_logs')
    request_type = models.CharField(max_length=100, help_text="Pvž., 'feedback_generation', 'feedback_analysis'")
    model_name = models.CharField(max_length=100)
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_cost = models.DecimalField(max_digits=15, decimal_places=10, default=0.0)
    raw_response = models.JSONField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.request_type} by {self.user} ({self.total_cost}$)"

class GlobalSettings(models.Model):
    personal_form_enabled = models.BooleanField(default=True, help_text="Įjungti 'Individuali forma' funkcionalumą visai platformai.")
    team_form_enabled = models.BooleanField(default=True, help_text="Įjungti 'Komandinė forma' funkcionalumą visai platformai.")

    class Meta:
        verbose_name_plural = "Global Settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super(GlobalSettings, self).save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

class PageDescription(models.Model):
    # index.html
    index_hero_title = models.CharField(max_length=255, default="Skatinkite atvirą komandos kultūrą")
    index_hero_desc = models.TextField(default="Mūsų platforma padeda lengvai rinkti ir analizuoti atsiliepimus. Išryškinkite stiprybes ir padėkite savo darbuotojams augti kartu.")
    index_features_title = models.CharField(max_length=255, default="Kodėl verta rinktis mus?")
    index_feature1_title = models.CharField(max_length=255, default="Atviras Grįžtamasis Ryšys")
    index_feature1_desc = models.TextField(default="Skatinkite skaidrumą ir asmeninį augimą su atvirais, vardiniais kolegų atsiliepimais bei vertinimais.")
    index_feature2_title = models.CharField(max_length=255, default="Dirbtinio Intelekto Įžvalgos")
    index_feature2_desc = models.TextField(default="AI algoritmai sistemina gautus atsiliepimus, išryškindami asmenines stiprybes ir aiškias sritis, kuriose vertėtų tobulėti.")
    index_feature3_title = models.CharField(max_length=255, default="Paprasta Naudoti")
    index_feature3_desc = models.TextField(default="Intuityvi sąsaja tiek administratoriams, tiek darbuotojams. Pradėkite per kelias minutes.")
    index_howitworks_title = models.CharField(max_length=255, default="Kaip tai veikia?")
    index_step1_title = models.CharField(max_length=255, default="Paprašykite Atsiliepimo")
    index_step1_desc = models.TextField(default="Pasirinkite kolegą ir išsiųskite prašymą įvertinti jūsų darbą keliais paspaudimais.")
    index_step2_title = models.CharField(max_length=255, default="Gaukite Įvertinimą")
    index_step2_desc = models.TextField(default="Kolegos atvirai atsako į išsamius kompetencijų ir asmeninių savybių klausimus.")
    index_step3_title = models.CharField(max_length=255, default="Analizuokite su AI")
    index_step3_desc = models.TextField(default="Dirbtinis intelektas praskenuoja komentarus ir pateikia aiškias stiprybes bei tobulėjimo sritis.")
    index_cta_title = models.CharField(max_length=255, default="Pasiruošę pagerinti komandos ryšį?")
    index_cta_desc = models.TextField(default="Prisijunkite prie įmonių, kurios naudoja atsiliepimus savo augimui skatinti. Pradėkite nemokamą bandomąjį laikotarpį šiandien.")

    # apie_mus.html
    about_hero_title = models.CharField(max_length=255, default="Apie Mūsų Komandą")
    about_hero_desc = models.TextField(default="Orbigrow.lt tikslas – padėti organizacijoms sukurti atvirą grįžtamojo ryšio kultūrą ir paskatinti kiekvieno darbuotojo augimą.")
    about_mission_title = models.CharField(max_length=255, default="Mūsų Misija")
    about_mission_desc1 = models.TextField(default="Tikime, kad nuolatinis ir atviras kolegų vertinimas yra pagrindinis komandos tobulėjimo variklis. Dažnai grįžtamasis ryšys įmonėse būna pamirštamas, paliekamas tik metiniams pokalbiams arba anoniminis, kas trukdo konstruktyviam dialogui.")
    about_mission_desc2 = models.TextField(default="Mūsų platforma sprendžia šią problemą siūlydama patogų, vardinį ir struktūrizuotą atsiliepimų rinkimo procesą, kurį papildo modernus dirbtinis intelektas (AI), išryškinantis esmines stiprybes bei pastangas.")
    about_values_title = models.CharField(max_length=255, default="Mūsų Vertybės")
    about_values_subtitle = models.CharField(max_length=255, default="Principai, kuriais vadovaujamės kurdami platformą")
    about_value1_title = models.CharField(max_length=255, default="Skaidrumas")
    about_value1_desc = models.TextField(default="Mes nesislepiame už anonimiškumo. Tikime, kad tikras tobulėjimas prasideda nuo atviro ir nuoširdaus grįžtamojo ryšio.")
    about_value2_title = models.CharField(max_length=255, default="Inovacijos")
    about_value2_desc = models.TextField(default="AI integracija leidžia sutaupyti valandas laiko analizuojant dešimtis komentarų, paverčiant juos aiškiomis įžvalgomis.")
    about_value3_title = models.CharField(max_length=255, default="Paprastumas")
    about_value3_desc = models.TextField(default="Platforma sukurta taip, kad prašyti ir suteikti grįžtamąjį ryšį užtruktų vos kelis paspaudimus.")
    about_value4_title = models.CharField(max_length=255, default="Palaikymas")
    about_value4_desc = models.TextField(default="Mūsų tikslas ne kritikuoti, o auginti. Viskas orientuota į komandos nario stiprybių ugdymą.")

    # saugumas.html
    security_content = models.TextField(default="""<h2>Mūsų saugumo praktikos</h2><p>Čia pateikiama informacija apie tai, kaip saugome jūsų duomenis.</p>""")

    class Meta:
        verbose_name_plural = "Page Descriptions"

    def save(self, *args, **kwargs):
        self.pk = 1
        super(PageDescription, self).save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

