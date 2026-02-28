import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'feedbackas.settings')
django.setup()
from django.template.loader import render_to_string
from feedbackas.models import FeedbackRequest

print("Rendering template...")
try:
    print(render_to_string('my_tasks.html', {}).split('id="editModal"')[1][:500])
except Exception as e:
    print(f"Error: {e}")
