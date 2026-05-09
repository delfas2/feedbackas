from django import template
from django.utils.translation import get_language

register = template.Library()

@register.filter
def translate_field(obj, field_name):
    """
    Grąžina lauko reikšmę priklausomai nuo aktyvios kalbos.
    Pvz., jei kalba 'en', ieškos '{field_name}_en'.
    Naudojimas šablone: {{ page_description|translate_field:'index_hero_title' }}
    """
    lang = get_language()
    
    if lang == 'en':
        en_field = f"{field_name}_en"
        en_value = getattr(obj, en_field, None)
        if en_value:
            return en_value
            
    # Fallback to default (LT)
    return getattr(obj, field_name, '')

@register.filter
def translate_project(name):
    if name == 'Atsiliepimas':
        from django.utils.translation import gettext as _
        return _('Atsiliepimas')
    return name
