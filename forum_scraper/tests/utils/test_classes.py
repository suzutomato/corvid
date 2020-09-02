# -*- coding: utf-8 -*-
from copy import deepcopy

import pytest

from forum_scraper.utils.classes import (
    OrderedSet,
    URLOrderedSet
)

FAKE_DATA_PATH = '/'
FAKE_THD_DIR_TMPLT = '{start_time}-{topic_id}'
FAKE_THD_CONT_TMPLT = '{start_time}-{topic_id}.tsv'
FAKE_EXPTR_KWARGS = {'foo': 'bar'}


@pytest.fixture
def ref():
    return list(range(1, 11))


@pytest.fixture
def os(ref):
    return OrderedSet(ref)


class TestOrderedSet:

    def test_len(self, os, ref):
        assert len(os) == len(ref)

    def test_contains(self, os, ref):
        a = ref[0]
        assert (a in os) == (a in ref)

    def test_getitem(self, os, ref):
        assert os[0] == ref[0]
        assert os[-1] == ref[-1]
        assert os[:3] == OrderedSet(ref[:3])
        assert os[::2] == OrderedSet(ref[::2])

    def test_iter(self, os, ref):
        assert list(os) == ref

    def test_eq(self, os, ref):
        os_copy = deepcopy(os)
        assert os == os_copy
        assert os == ref
        assert os == set(ref)

    def test_add(self, os, ref):
        os_copy = deepcopy(os)
        ref_copy = deepcopy(ref)
        os_copy.add(100)
        ref_copy.append(100)
        assert os_copy[-1] == 100
        assert list(os_copy) == ref_copy

    def test_add_before(self, os, ref):
        os_copy, ref_copy = deepcopy(os), deepcopy(ref)
        index = len(ref) // 2
        key = ref[index]
        os_copy.add_before(key, 100)
        ref_copy.insert(index, 100)
        assert list(os_copy) == ref_copy

    def test_add_after(self, os, ref):
        os_copy, ref_copy = deepcopy(os), deepcopy(ref)
        index = len(ref) // 2
        key = ref[index]
        os_copy.add_after(key, 100)
        ref_copy.insert(index+1, 100)
        assert list(os_copy) == ref_copy

    def test_discard(self, os, ref):
        os_copy, ref_copy = deepcopy(os), deepcopy(ref)
        index = 3
        key = ref[3]
        os_copy.discard(key)
        ref_copy.pop(index)
        assert list(os_copy) == ref_copy
        assert len(os_copy) == len(ref_copy)  # self.map has to be updated

    def test_pop(self, os, ref):
        # Pop from last
        os_copy, ref_copy = deepcopy(os), deepcopy(ref)
        assert os_copy.pop() == ref_copy[-1]
        assert os_copy.pop(last=False) == ref_copy[0]
        assert list(os_copy) == ref_copy[1:-1]

    def test_key_errors(self, os, ref):
        os_copy = deepcopy(os)
        key = os_copy[-1] + 1
        with pytest.raises(KeyError):
            os_copy.add_before(key, 100)

        with pytest.raises(KeyError):
            os_copy.add_after(key, 100)

        os_new = OrderedSet()
        with pytest.raises(KeyError):
            os_new.pop()


class TestURLOrderedSet:
    def test_init(self):
        uos = URLOrderedSet()
        assert uos.pivot_url is None
        assert len(uos) == 0

    def test_init_with_iterable(self, ref):
        uos = URLOrderedSet(ref, ref[0])
        assert uos.pivot_url == ref[0]
        assert list(uos) == ref

    def test_set_pivot_url(self, ref):
        uos = URLOrderedSet(iterable=ref)
        uos.set_pivot_url()
        assert uos.pivot_url == ref[0]

        uos.set_pivot_url(ref[1])
        assert uos.pivot_url == ref[1]

    def test_add(self):
        uos = URLOrderedSet()

        uos.add_url('url1')
        assert list(uos) == ['url1']

        uos.add_url('url2')
        assert list(uos) == ['url1', 'url2']

        uos.pivot_url = 'url2'
        uos.add_url('url3')
        assert list(uos) == ['url1', 'url3', 'url2']
        uos.add_url('url4')
        assert list(uos) == ['url1', 'url3', 'url4', 'url2']

    def test_trim(self):
        uos = URLOrderedSet(range(100))
        max_length = 70
        uos.trim(max_length)
        assert len(uos) == max_length
        assert list(uos) == list(range(max_length))

        max_length = 40
        uos.trim(max_length)
        assert len(uos) == max_length
        assert list(uos) == list(range(max_length))
