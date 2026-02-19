from django import template
from users.models import Profile

register = template.Library()

@register.filter
def user_avatar(user):
    try:
        if hasattr(user, 'profile'):
            if user.profile.image:
                return user.profile.image.url
    except Profile.DoesNotExist:
        # Create profile if it doesn't exist (self-healing)
        Profile.objects.create(user=user)
        return '/media/default.jpg'  # Assuming default exists or is served
    except Exception:
        pass
    
    # Return a safe default placeholder if anything fails
    return f"https://placehold.co/40x40/eee/333?text={user.username[0].upper()}"
