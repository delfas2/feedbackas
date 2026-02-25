import os
import sys
import django

sys.path.append('/Users/justinaszamarys/Library/Mobile Documents/com~apple~CloudDocs/_Python_duomenys/docker_powerup/feedbackas')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'feedbackas.settings')

django.setup()

from feedbackas.models import Feedback
from feedbackas.ai_service import FeedbackGenerator

def backfill():
    import time
    feedbacks = Feedback.objects.all()
    count = feedbacks.count()
    print(f"Found {count} feedbacks to backfill.")
    
    for i, fb in enumerate(feedbacks):
        # Skip if already extracted
        if getattr(fb, 'extracted_strengths', None) or getattr(fb, 'extracted_improvements', None):
            print(f"[{i+1}/{count}] Feedback {fb.id} already extracted, skipping.")
            continue
            
        print(f"[{i+1}/{count}] Extracting for Feedback {fb.id}...")
        extracted_data = FeedbackGenerator.extract_strengths_weaknesses(fb.feedback, fb.comments)
        fb.extracted_strengths = extracted_data.get("strengths", [])
        fb.extracted_improvements = extracted_data.get("improvements", [])
        fb.save()
        print(f"   -> Saved: {len(fb.extracted_strengths)} strengths, {len(fb.extracted_improvements)} improvements.")
        
        # Avoid hitting the 10 requests / min Free Tier quota
        time.sleep(7)
        
    print("Done!")

if __name__ == '__main__':
    backfill()
