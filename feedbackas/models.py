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

