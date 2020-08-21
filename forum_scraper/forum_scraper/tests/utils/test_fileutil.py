# -*- coding: utf-8 -*-
import pytest

from forum_scraper.utils import fileutil
from forum_scraper.tests.statics import (
    VALID_COMMENT_ID,
    VALID_TOPIC_ID,
    VALID_FORUM_ID
)


class TestGetParentId:
    # ------------
    # Valid inputs
    # ------------
    @pytest.mark.parametrize('input,expected', [
        ('id', 'id'),
        ('prefix_suffix', 'prefix'),
        (None, None),
        (VALID_FORUM_ID, VALID_FORUM_ID),  # Forum ID -> Forum ID
        (VALID_TOPIC_ID, VALID_FORUM_ID),  # Topic ID -> Forum ID
        (VALID_COMMENT_ID, VALID_TOPIC_ID)  # Comment ID -> Topic ID
    ])
    def test_valid_inputs(self, input, expected):
        actual = fileutil.get_parent_id(input)
        assert actual == expected

    # ------------
    # TypeError
    # ------------
    @pytest.mark.parametrize('input', [[], {}, set(), 1, 1.4, True, b''])
    def test_type_error(self, input):
        with pytest.raises(TypeError):
            fileutil.get_parent_id(input)


class TestGetTemplateKwargs:
    # ------------
    # Valid inputs
    # ------------
    CMT_ID = VALID_COMMENT_ID
    TPC_ID = VALID_TOPIC_ID
    FRM_ID = VALID_FORUM_ID

    @pytest.mark.parametrize('item,exp_ids', [
        ({}, (None, None, None)),  # Empty -> All None
        ({'comment_id': CMT_ID}, (CMT_ID, TPC_ID, FRM_ID)),  # CMT_ID -> All
        ({'topic_id': TPC_ID}, (None, TPC_ID, FRM_ID)),  # TPC_ID -> TPC, FRM
        ({'forum_id': FRM_ID}, (None, None, FRM_ID)),  # FRM_ID -> only FRM_ID
        ({'comment_id': CMT_ID, 'forum_id': FRM_ID+'-B'},
         (CMT_ID, TPC_ID, FRM_ID+'-B'))  # Should take the provided parent ID
    ])
    def test_valid_inputs(self, item, exp_ids):
        actual = fileutil.get_template_kwargs(item)
        exp_cmt_id, exp_tpc_id, exp_frm_id = exp_ids
        assert actual['comment_id'] == exp_cmt_id
        assert actual['topic_id'] == exp_tpc_id
        assert actual['forum_id'] == exp_frm_id


class TestPickles:

    def test_read_non_exisiting(self, tmp_path):
        p = tmp_path / 'pickle' / 'not_exists.pickle'
        default = {}

        # Read from non-exising path -> return default
        s = fileutil.read_pickle(p, default)
        assert s is default

    def test_round_trip(self, tmp_path):
        p = tmp_path / 'pickle' / 'round_trip.pickle'
        default = 0
        fake_obj = {'test': 1000}

        fileutil.to_pickle(fake_obj, p)
        o = fileutil.read_pickle(p, default)

        assert o == fake_obj
