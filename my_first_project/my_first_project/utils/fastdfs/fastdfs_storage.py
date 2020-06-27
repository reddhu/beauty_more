from django.core.files.storage import Storage
from django.conf import settings


class FastDFSStorage(Storage):
    def save(self, name, content, max_length=None):
        return None

    def open(self, name, mode='rb'):
        return None

    def exists(self, name):
        return False

    def url(self, name):
        return settings.FDFS_URL + name
