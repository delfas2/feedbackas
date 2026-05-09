import re

with open('templates/home.html', 'r') as f:
    content = f.read()

# Fix the double trans error and incorrect verbatim nesting
content = content.replace('{% trans "{% endverbatim %}{% trans "Kraunama..." %}{% verbatim %}" %}', '{% endverbatim %}{% trans "Kraunama..." %}{% verbatim %}')
content = content.replace('{% trans "{% endverbatim %}{% trans "Grįžtamojo ryšio dar nėra." %}{% verbatim %}" %}', '{% endverbatim %}{% trans "Grįžtamojo ryšio dar nėra." %}{% verbatim %}')
content = content.replace('{% trans "{% endverbatim %}{% trans "Kaip pradėti" %}{% verbatim %}" %}', '{% endverbatim %}{% trans "Kaip pradėti" %}{% verbatim %}')

with open('templates/home.html', 'w') as f:
    f.write(content)

print("Fixed home.html verbatim tags")
