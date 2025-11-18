from django.db import models
from django.contrib.auth.models import User

class FeedbackRequest(models.Model):
    requester = models.ForeignKey(User, related_name='made_requests', on_delete=models.CASCADE)
    requested_to = models.ForeignKey(User, related_name='received_requests', on_delete=models.CASCADE)
    project_name = models.CharField(max_length=255)
    due_date = models.DateField()
    status = models.CharField(max_length=20, default='pending')

    def __str__(self):
        return f"Feedback request from {self.requester} to {self.requested_to} for {self.project_name}"

class Feedback(models.Model):
    feedback_request = models.OneToOneField(FeedbackRequest, on_delete=models.CASCADE)
    rating = models.IntegerField()
    keywords = models.CharField(max_length=255)
    feedback = models.TextField()

    def __str__(self):
        return f"Feedback for {self.feedback_request}"
