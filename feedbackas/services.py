from django.conf import settings
from django.db.models import Avg
from .models import Feedback, FeedbackRequest
from django.contrib.auth.models import User

class FeedbackAnalytics:
    @staticmethod
    def get_user_stats(user, period='all'):
        """
        Apskaičiuoja vartotojo atsiliepimų statistiką ir kompetencijų vidurkius.
        """
        from django.utils import timezone
        import datetime
        
        filters = {
            'feedback_request__requester': user,
            'feedback_request__status': 'completed'
        }
        
        now = timezone.now()
        if period == 'month':
            filters['feedback_request__created_at__gte'] = now - datetime.timedelta(days=30)
        elif period == 'quarter':
            filters['feedback_request__created_at__gte'] = now - datetime.timedelta(days=90)
        elif period == 'year':
            filters['feedback_request__created_at__gte'] = now - datetime.timedelta(days=365)
            
        completed_feedback = Feedback.objects.filter(**filters)
        completed_feedback_count = completed_feedback.count()
        
        # Participation Rate
        total_requests_filters = {'requester': user}
        if period == 'month':
            total_requests_filters['created_at__gte'] = now - datetime.timedelta(days=30)
        elif period == 'quarter':
            total_requests_filters['created_at__gte'] = now - datetime.timedelta(days=90)
        elif period == 'year':
            total_requests_filters['created_at__gte'] = now - datetime.timedelta(days=365)
        
        total_requests = FeedbackRequest.objects.filter(**total_requests_filters).count()
        participation_rate = 0
        if total_requests > 0:
            participation_rate = int((completed_feedback_count / total_requests) * 100)
            
        overall_avg_rating = completed_feedback.aggregate(Avg('rating'))['rating__avg'] or 0
        
        # Top % In Company
        top_percentile = '--'
        if hasattr(user, 'profile') and user.profile.company_link:
            company = user.profile.company_link
            company_users = User.objects.filter(profile__company_link=company)
            
            user_scores = []
            for u in company_users:
                u_filters = {
                    'feedback_request__requester': u,
                    'feedback_request__status': 'completed'
                }
                if period == 'month':
                    u_filters['feedback_request__created_at__gte'] = now - datetime.timedelta(days=30)
                elif period == 'quarter':
                    u_filters['feedback_request__created_at__gte'] = now - datetime.timedelta(days=90)
                elif period == 'year':
                    u_filters['feedback_request__created_at__gte'] = now - datetime.timedelta(days=365)
                    
                u_avg = Feedback.objects.filter(**u_filters).aggregate(Avg('rating'))['rating__avg'] or 0
                if u_avg > 0:
                    user_scores.append(u_avg)
                    
            if user_scores and overall_avg_rating > 0:
                user_scores.sort(reverse=True)
                if overall_avg_rating in user_scores:
                    rank = user_scores.index(overall_avg_rating) + 1
                    percentile_calc = int((rank / len(user_scores)) * 100)
                    top_percentile = percentile_calc if percentile_calc > 0 else 1
        
        all_keywords = []
        all_strengths = []
        all_improvements = []
        
        for feedback in completed_feedback:
            keywords = [kw.strip() for kw in feedback.keywords.split(',') if kw.strip()]
            all_keywords.extend(keywords)
            
            # Sumuojame AI išskirtas savybes
            if isinstance(feedback.extracted_strengths, list):
                all_strengths.extend(feedback.extracted_strengths)
            if isinstance(feedback.extracted_improvements, list):
                all_improvements.extend(feedback.extracted_improvements)

        competency_averages = completed_feedback.aggregate(
            teamwork=Avg('teamwork_rating'),
            communication=Avg('communication_rating'),
            initiative=Avg('initiative_rating'),
            technical_skills=Avg('technical_skills_rating'),
            problem_solving=Avg('problem_solving_rating')
        )
        competencies = [
            {'name': 'Komandinis Darbas', 'score': round(competency_averages.get('teamwork') or 0, 2)},
            {'name': 'Komunikacija', 'score': round(competency_averages.get('communication') or 0, 2)},
            {'name': 'Iniciatyvumas', 'score': round(competency_averages.get('initiative') or 0, 2)},
            {'name': 'Techninės Žinios', 'score': round(competency_averages.get('technical_skills') or 0, 2)},
            {'name': 'Problemų Sprendimas', 'score': round(competency_averages.get('problem_solving') or 0, 2)},
        ]

        training_map = {
            'Komandinis Darbas': 'Mokymai apie efektyvų komandinį darbą',
            'Komunikacija': 'Viešojo kalbėjimo ir komunikacijos įgūdžių mokymai',
            'Iniciatyvumas': 'Proaktyvumo ir iniciatyvumo skatinimo seminaras',
            'Techninės Žinios': 'Specializuoti techniniai kursai pagal Jūsų sritį',
            'Problemų Sprendimas': 'Kritinio mąstymo ir problemų sprendimo dirbtuvės',
        }
        
        recommended_trainings = []
        for competency in competencies:
            if competency['score'] < 7:
                recommended_trainings.append({
                    'competency': competency['name'],
                    'training': training_map.get(competency['name'], 'Bendrieji tobulinimosi kursai')
                })
        
        return {
            'overall_avg_rating': round(overall_avg_rating, 2),
            'received_feedback_count': completed_feedback_count,
            'participation_rate': participation_rate,
            'top_percentile': top_percentile,
            'all_keywords': list(set(all_keywords))[:7],
            'competencies': competencies,
            'strengths': all_strengths[:5],
            'improvements': all_improvements[:5],
            'recommended_trainings': recommended_trainings,
        }