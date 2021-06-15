# Naive implementation of LFU cache by The Internet:tm: and my puny brain.
# Open for a better implementation by opening an issue and put `[LFU cache]` on the topic/issue name
from collections import deque


class LFUCache(object):
    """
    Class that implement LFU algorithm.
    Based on Deque data structure for fast operations and ordering reasons.
    """
    # TODO: Make LFUCache **subclass** of Deque as this class implementation **will**
    # be based on Deque at some point.
    def __init__(self, size=1024):
        """
        Create a new LFUCache instance for caching

        :param size: Size of the cache. Defaults to 1024 entries.
        """
        # Deque because
        # - I learned that from computer science class (unfortunately)
        # - you can left append it and not having to do those awful shifting dances
        # - you can pop any direction you want
        # - tried and tested (have you googled Deque?)
        # - IT HAS ROTATE FUNCTION WTF.
        # - it's in Python stdlib so why reimplementing it from scratch?
        self.cache = deque({})
        # dict because
        # - it's the next best thing to use as an index (which LRU cache depends on)
        # - key=value support, which is **awesome**
        # - included in Python stdlib
        # - work around limitations with object searching (require searching for attribute)
        # Index is **NEVER** used for data fetching/delete, they're just to work around a few
        # limitations
        self.index = []
        # Set the upper element size limit of cache
        self.size = size

    def _get_cache_metadata_template(self):
        """
        Base template for cache metadata

        :return: Template cache data
        """
        base_dict = {'data': None, 'hit_count': 0}
        return base_dict

    def _get_cache_index_template(self):
        base_index = {'name': None}
        return base_index

    def _get_index_by_name(self, name):
        # Hinty hint the cache_entry as dict as every entry in cache is a dict
        cache_entry: dict
        # This might sounds awfully weird, but it is how it is.
        # Deque index only matches the whole object, irrespective of the contents.
        # So do a classic O(n) traversing (what's performance?) and check the name attribute,
        # get the whole dict if exists, __then__ get the actual index
        for cache_entry in self.cache:
            if cache_entry.get('name') == name:
                return self.cache.index(cache_entry)

    def insert(self, name, data):
        """
        Insert new data.

        :param name: Name of the key
        :param data: Data that the key represents.
        :return: New data containing key and metadata
        """
        new_cache_object = self._get_cache_metadata_template()
        new_cache_index = self._get_cache_index_template()
        if name not in self.cache:
            new_cache_object = self._get_cache_metadata_template()
            new_cache_object.data = data
            self.cache.appendleft(new_cache_object)
            new_cache_index.update({'name': name})
            self.index.append(name)
        elif name in self.index:
            # Call update function instead
            self.update(name, data)
        return

    def update(self, name, data):
        # Treat as update.
        updated_cache_index = self.index.get(name)
        updated_cache_object = self.cache.get(name)
        self.cache.remove(self.index.get(name).get('data'))
        updated_cache_object.name = name
        updated_cache_object.data = data
        self.cache.appendleft(updated_cache_object)
        updated_cache_index.update({'data': updated_cache_object})
        self.index.update({name: updated_cache_index})


    def get(self, name):
        pass

    def check(self, name, data):
        if name in self.cache:
            return True
        return False

    def prune(self):
        while len(self.cache) > self.size:
            self.cache.pop()

