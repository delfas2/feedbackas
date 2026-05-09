import re

with open('templates/all_feedback_list.html', 'r') as f:
    content = f.read()

if '{% load i18n %}' not in content:
    content = content.replace("{% extends 'base.html' %}", "{% extends 'base.html' %}\n{% load i18n %}")

content = content.replace('Visi įvertinimai', '{% trans "Visi įvertinimai" %}')
content = content.replace('Visų platformoje pateiktų įvertinimų sąrašas', '{% trans "Visų platformoje pateiktų įvertinimų sąrašas" %}')
content = content.replace('Įvertinimų istorija', '{% trans "Įvertinimų istorija" %}')
content = content.replace('Vertinamas asmuo', '{% trans "Vertinamas asmuo" %}')
content = content.replace('Vertintojas', '{% trans "Vertintojas" %}')
content = content.replace('Projektas', '{% trans "Projektas" %}')
content = content.replace('Data', '{% trans "Data" %}')
content = content.replace('Įvertinimas', '{% trans "Įvertinimas" %}')
content = content.replace('Užpildytų vertinimų nerasta.', '{% trans "Užpildytų vertinimų nerasta." %}')

with open('templates/all_feedback_list.html', 'w') as f:
    f.write(content)

print("Updated all_feedback_list.html")
