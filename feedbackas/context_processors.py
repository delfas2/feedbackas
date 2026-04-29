from .models import GlobalSettings

def global_settings_processor(request):
    try:
        settings = GlobalSettings.load()
    except Exception:
        settings = None
    return {'global_settings': settings}
