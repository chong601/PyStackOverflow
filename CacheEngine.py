# Naive implementation of LFU cache by The Internet:tm: and my puny brain.
# Open for a better implementation by opening an issue and put `[LFU cache]` on the topic/issue name
from collections import OrderedDict
import datetime


class LFUCache(object):

    def __init__(self, size=1024, lifetime=0):
        """
        Create a new LFUCache instance for caching

        :param size: Size of the cache. Defaults to 1024 entries.
        :param lifetime: Optional. Lifetime of the entry. Converts this LFU cache implementation into a hybrid
        LFU/LRU cache implementation.
        """
        self.cache = {}
        self.size = size
        self.lifetime = lifetime
        self._enable_lru = True if self.lifetime > 0 else False

    def _get_cache_template(self):
        """
        Base template for cache metadata

        :return: Template cache data
        """
        base_dict = {'data': None, 'hit_count': 0}
        if self._enable_lru:
            base_dict.update({'expire': self._get_new_expiry()})
        return base_dict

    def _get_new_expiry(self):
        """
        Returns new expiry time based on current time

        :return: `datetime` object containing updated time
        """
        return datetime.datetime.now() + datetime.timedelta(seconds=self.lifetime)

    def insert(self, name, data):
        """
        Insert new data.

        :param name: Name of the key
        :param data: Data that the key represents.
        :return: New data containing key and metadata
        """
        new_data = None
        if name not in self.cache:
            new_data = self._get_cache_template()
            new_data['data'] = data
            self.cache.update({name, new_data})
        return new_data

    def check(self, name):
        if name in self.cache:
            expiry = self.cache[name].get('expiry')
            if datetime.datetime.now() <= expiry:
                self.cache[name].update({'expiry': self._get_new_expiry()})
                return self.cache[name]['data']
            else:
                self.delete(name)
        return None

    def delete(self, name):
        self.cache.pop(name)
