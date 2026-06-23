from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        import users.signals
        
        try:
            from auditlog.registry import auditlog
            from django.contrib.auth.models import User
            from users.models import Company, Profile, Department, EmployeeCountLog, ContractSettings
            from feedbackas.models import Feedback, FeedbackRequest, GlobalSettings
            
            # Registering User models
            auditlog.register(User)
            auditlog.register(Company)
            auditlog.register(Profile)
            auditlog.register(Department)
            auditlog.register(EmployeeCountLog)
            auditlog.register(ContractSettings)
            
            # Registering Feedback models
            auditlog.register(Feedback)
            auditlog.register(FeedbackRequest)
            auditlog.register(GlobalSettings)
        except ImportError:
            pass
