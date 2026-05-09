import re
import os

templates = [
    'templates/my_tasks.html',
    'templates/fill_feedback.html',
    'templates/all_feedback_list.html'
]

# Pattern for {{ ...project_name }}
# We replace it with a conditional translation for the default 'Atsiliepimas'
for t_path in templates:
    if not os.path.exists(t_path): continue
    with open(t_path, 'r') as f:
        content = f.read()
    
    # Handle both request.project_name and feedback_request.project_name and feedback.feedback_request.project_name
    def replacer(match):
        prefix = match.group(1)
        return '{% if ' + prefix + 'project_name == "Atsiliepimas" %}{% trans "Atsiliepimas" %}{% else %}{{ ' + prefix + 'project_name }}{% endif %}'

    # Match {{ (optional_prefix)project_name }}
    new_content = re.sub(r'\{\{\s*([\w\.]*)project_name\s*\}\}', replacer, content)
    
    # Also handle data attributes like data-project="{{ ...project_name }}"
    # In data attributes, we might want just the string or the translated string
    # For modals, we should probably translate it too.
    
    with open(t_path, 'w') as f:
        f.write(new_content)

print("Updated templates to handle project_name translation")
