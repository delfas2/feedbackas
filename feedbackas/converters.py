from django.conf import settings
from hashids import Hashids

class HashIdConverter:
    regex = '[a-zA-Z0-9]+'

    def __init__(self):
        # We need to set a minimum length so IDs don't look like '1' or '2'
        self.hashids = Hashids(salt=settings.HASHIDS_SALT, min_length=4)

    def to_python(self, value):
        decoded = self.hashids.decode(value)
        if decoded:
            return decoded[0]
        raise ValueError

    def to_url(self, value):
        return self.hashids.encode(int(value))
