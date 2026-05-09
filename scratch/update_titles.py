import re
import os

files = [
    'templates/base.html',
    'templates/home.html',
    'templates/results.html',
    'templates/team_members.html',
    'templates/team_statistics.html',
    'templates/my_tasks.html',
    'templates/all_feedback_list.html',
    'templates/company_management.html',
    'templates/team_member_detail.html',
    'templates/questionnaires/list.html',
    'templates/questionnaires/statistics.html',
    'templates/fill_feedback.html',
]

for path in files:
    if not os.path.exists(path): continue
    with open(path, 'r') as f:
        content = f.read()
    
    # 1. Wrap block title content
    content = re.sub(r'\{% block title %\}(.*?)\{% endblock %\}', r'{% block title %}{% trans "\1" %}{% endblock %}', content)
    
    with open(path, 'w') as f:
        f.write(content)

print("Updated titles in templates")
