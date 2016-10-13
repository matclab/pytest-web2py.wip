# -*- coding: utf-8 -*-

import logging
import pytest
import os

from gluon.languages import safe_eval

logger = logging.getLogger("web2py.test")
logger.setLevel(logging.DEBUG)

# Dictionnary that, for each language, old words which translation let the
# spelling unchange.
same_translation = {
    'fr': [
        '!=',
        '<',
        '<=',
        '=',
        '>',
        '>=',
        '?',
        'Actions',
        'Admin',
        'Auth cases',
        'Auth events',
        'Auth groups',
        'Auth memberships',
        'Auth permissions',
        'Auth users',
        'CSV',
        'Cache',
        'Code',
        'Config.ini',
        'Copyright',
        'Databases',
        'Date',
        'Description',
        'Documentation',
        'E-mail',
        'Email',
        'Export:',
        'FAQ',
        'First users',
        'HTML',
        'ID',
        'IDs',
        'Id',
        'Index',
        'Info',
        'Init',
        'Introduction',
        'Items',
        'JSON',
        'Message',
        'Messages',
        'Nb. IDs',
        'Permission',
        'Permissions',
        'Plugins',
        'Python',
        'RAM',
        'Service',
        'Services',
        'Support',
        'Ticket',
        'Total',
        'Traceback',
        'Twitter',
        'URL',
        'Web2py',
        'XML',
        'admin',
        'cache',

    ],
}


def read_lang(lang, appdir):
    with open(os.path.join(appdir, 'languages/%s.py' % lang)) as lang_file:
        lang_text = lang_file.read().replace('\r\n', '\n').replace('@markmin\x01', '')
        return eval(lang_text)


def describe_translation():

    @pytest.mark.parametrize('lang', ['fr'])
    def everything_translated(appdir, lang):
        """ Check that every message is translated in `lang` languages files,
        except for message in `same_translation`.
        """
        lang_dict = read_lang(lang, appdir)
        for k in same_translation['fr']:
            lang_dict.pop(k, None)
        untranslated = [k for k in lang_dict if k == lang_dict[k]]
        logger.debug('\n'.join(untranslated))
        assert not untranslated


