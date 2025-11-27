from django.db import models
from django.contrib.auth.models import User

class FeedbackRequest(models.Model):
    requester = models.ForeignKey(User, related_name='made_requests', on_delete=models.CASCADE)
    requested_to = models.ForeignKey(User, related_name='received_requests', on_delete=models.CASCADE)
    project_name = models.CharField(max_length=255)
    comment = models.TextField(blank=True, null=True)
    due_date = models.DateField()
    status = models.CharField(max_length=20, default='pending')

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

    def __str__(self):
        return f"Feedback for {self.feedback_request}"
