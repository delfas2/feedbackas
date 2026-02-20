import os
import django
import random
from faker import Faker
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'feedbackas.settings')
django.setup()

from django.contrib.auth.models import User
from users.models import Company, Profile
from feedbackas.models import Questionnaire, FeedbackRequest, Feedback, Trait

fake = Faker('lt_LT')

def run():
    print("Starting fake data generation...")
    # 1. Create a Company
    company, _ = Company.objects.get_or_create(name='UAB PowerUp Fakers')
    
    # Pre-create some traits
    trait_names = ['Komunikabilus', 'Iniciatyvus', 'Atsakingas', 'Greitas', 'Kruopštus', 'Lyderis', 'Analitiškas', 'Lankstus', 'Inovatyvus', 'Empatiškas']
    traits = []
    for t in trait_names:
        tr, _ = Trait.objects.get_or_create(name=t)
        traits.append(tr)

    users = []
    print("Creating 100 users...")
    for i in range(100):
        first_name = fake.first_name()
        last_name = fake.last_name()
        username = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 99999)}"
        email = f"{username}@powerup.lt"
        
        user = User.objects.create_user(username=username, email=email, password='password123', first_name=first_name, last_name=last_name)
        # Profile is auto-created by signals, we just update it
        user.profile.company_link = company
        user.profile.save()
        users.append(user)

    print("Creating 1 questionnaire and 10-20 feedbacks per user...")
    for user in users:
        # Create 1 questionnaire
        q = Questionnaire.objects.create(title='360 Laipsnių Metinis Vertinimas', created_by=user)
        q.traits.set(random.sample(traits, 5))
        
        # Determine how many feedbacks this user received (10 to 20)
        num_feedbacks = random.randint(10, 20)
        
        # Select random reviewers from other users
        potential_reviewers = [u for u in users if u != user]
        reviewers = random.sample(potential_reviewers, min(len(potential_reviewers), num_feedbacks))
        
        for reviewer in reviewers:
            # Random date within the last year
            days_ago = random.randint(1, 365)
            created_date = timezone.now() - timedelta(days=days_ago)

            # Create Feedback Request
            fr = FeedbackRequest.objects.create(
                requester=user,
                requested_to=reviewer,
                project_name=q.title,
                comment='Prašome įvertinti mano metinius darbo rezultatus.',
                due_date=created_date.date() + timedelta(days=14),
                status='completed'
            )
            # Override created_at since it's an auto_now_add field
            FeedbackRequest.objects.filter(id=fr.id).update(created_at=created_date)

            # Generate random but realistic scores (weighted towards upper end to look like a real app)
            overall = random.choice([3, 4, 4, 5, 5])
            teamwork = random.choice([3, 4, 5])
            comms = random.choice([2, 3, 4, 5])
            init = random.choice([2, 3, 4])
            tech = random.choice([3, 4, 5])
            prob = random.choice([3, 4, 5])
            
            # Keywords
            selected_traits = random.sample(trait_names, random.randint(1, 4))
            keywords = ', '.join(selected_traits)
            
            Feedback.objects.create(
                feedback_request=fr,
                rating=overall,
                teamwork_rating=teamwork,
                communication_rating=comms,
                initiative_rating=init,
                technical_skills_rating=tech,
                problem_solving_rating=prob,
                keywords=keywords,
                comments=fake.text(max_nb_chars=120),
                feedback=fake.text(max_nb_chars=300)
            )

    print("Fake data successfully generated.")

if __name__ == '__main__':
    run()
