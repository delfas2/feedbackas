import re

with open('feedbackas/services.py', 'r') as f:
    content = f.read()

if 'from django.utils.translation import gettext as _' not in content:
    content = 'from django.utils.translation import gettext as _\n' + content

# Update competency names in get_user_stats
content = content.replace("'name': 'Komandinis Darbas'", "'name': _('Komandinis Darbas')")
content = content.replace("'name': 'Komunikacija'", "'name': _('Komunikacija')")
content = content.replace("'name': 'Iniciatyvumas'", "'name': _('Iniciatyvumas')")
content = content.replace("'name': 'Techninės Žinios'", "'name': _('Techninės Žinios')")
content = content.replace("'name': 'Problemų Sprendimas'", "'name': _('Problemų Sprendimas')")

# Update competency names in get_team_stats and get_member_detailed_stats (they use same strings)
# Note: they might have different casing or spacing, but here they seem identical.

with open('feedbackas/services.py', 'w') as f:
    f.write(content)

print("Updated services.py with gettext")
