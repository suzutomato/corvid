# -*- coding: utf-8 -*-
from collections.abc import MutableSet

from itemadapter import ItemAdapter


class ItemBuffer:
    def __init__(self):
        self._headers_not_written = True
        self.buffer = []
        self.header = []
        self.delimiter = ';'  # Used to join a list when a field contains one

    def __iter__(self):
        for row in self.buffer:
            yield row

    def __len__(self):
        return len(self.buffer)

    def store(self, item):
        adapter = ItemAdapter(item)

        if self._headers_not_written:
            # Store field_names in a list to make sure the order stays the same
            self.header = adapter.field_names()
            self.buffer.append(adapter.field_names())
            self._headers_not_written = False

        temp = []
        for field in self.header:
            val = adapter.get(field)
            if isinstance(val, list):
                val = self.delimiter.join([str(v) for v in val])
            temp.append(val)

        self.buffer.append(temp)


class OrderedSet(MutableSet):

    def __init__(self, iterable=None):
        self.end = end = []
        end += [None, end, end]
        self.map = {}
        if iterable is not None:
            self |= iterable

    def __len__(self):
        return len(self.map)

    def __contains__(self, key):
        return key in self.map

    def __getitem__(self, key):
        if isinstance(key, slice):
            start, end, step = key.indices(len(self))
            return OrderedSet([self[i] for i in range(start, end, step)])

        if isinstance(key, int):
            if key >= len(self):
                raise KeyError()
            if key < 0:
                it = reversed(self)
                key = abs(key) - 1
            else:
                it = iter(self)

            [next(it) for _ in range(key)]
            return next(it)

    def __iter__(self):
        end = self.end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def __repr__(self):
        if not self:
            return '{}()'.format(self.__class__.__name__)
        else:
            return '{}({})'.format(self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, OrderedSet):
            return len(self) == len(other) and list(self) == list(other)
        return set(self) == set(other)

    def add(self, key):
        if key not in self.map:
            end = self.end
            curr = end[1]
            curr[2] = end[1] = self.map[key] = [key, curr, end]

    def add_before(self, target_key, new_key):
        if target_key not in self.map:
            raise KeyError()
        if new_key not in self.map:
            target = self.map[target_key]
            prev = target[1]
            prev[2] = target[1] = self.map[new_key] = [new_key, prev, target]

    def add_after(self, target_key, new_key):
        if target_key not in self.map:
            raise KeyError()
        if new_key not in self.map:
            target = self.map[target_key]
            next_val = target[2]
            next_val[1] = target[2] = self.map[new_key] = \
                [new_key, target, next_val]

    def discard(self, key):
        if key in self.map:
            key, prev, next_val = self.map[key]
            prev[2] = next_val
            next_val[1] = prev
            del self.map[key]

    def pop(self, last=True):
        if not self:
            raise KeyError('set is empty')
        key = self.end[1][0] if last else self.end[2][0]
        self.discard(key)
        return key


class URLOrderedSet(OrderedSet):
    def __init__(self, iterable=None, pivot_url=None):
        super().__init__(iterable)
        self.pivot_url = pivot_url

    def add_url(self, new_url):
        if self.pivot_url is None:
            self.add(new_url)
        else:
            self.add_before(self.pivot_url, new_url)

    def set_pivot_url(self, pivot_url=None):
        if not self:
            raise KeyError('set is empty')
        if pivot_url is None:
            self.pivot_url = self[0]
        elif pivot_url in self.map:
            self.pivot_url = pivot_url
        else:
            raise KeyError()

    def trim(self, max_length=1000):
        if len(self) > max_length:
            for _ in range(len(self) - max_length):
                self.pop()
