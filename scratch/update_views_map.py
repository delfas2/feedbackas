import re

with open('feedbackas/views.py', 'r') as f:
    content = f.read()

# Add English keys to the map
content = content.replace("'komandinis darbas': 'teamwork_rating',", "'komandinis darbas': 'teamwork_rating',\n        'teamwork': 'teamwork_rating',")
content = content.replace("'komunikacija': 'communication_rating',", "'komunikacija': 'communication_rating',\n        'communication': 'communication_rating',")
content = content.replace("'iniciatyvumas': 'initiative_rating',", "'iniciatyvumas': 'initiative_rating',\n        'initiative': 'initiative_rating',")
content = content.replace("'techninės žinios': 'technical_skills_rating',", "'techninės žinios': 'technical_skills_rating',\n        'technical knowledge': 'technical_skills_rating',")
content = content.replace("'problemų sprendimas': 'problem_solving_rating',", "'problemų sprendimas': 'problem_solving_rating',\n        'problem solving': 'problem_solving_rating',")

with open('feedbackas/views.py', 'w') as f:
    f.write(content)

print("Updated views.py competency map")
