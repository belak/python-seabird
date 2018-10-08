import pytest
import yaml

from seabird.irc import Message, Identity


def load_irc_fixture(fname):
    with open(f'irc-parser-tests/tests/{fname}.yaml') as f:
        return yaml.load(f)['tests']


@pytest.mark.parametrize('test', load_irc_fixture('msg-split'))
def test_message_parsing(test):
    atoms = test['atoms']

    msg = Message(test['input'])

    # Core messsage
    assert msg.event == atoms.pop('verb')
    assert msg.args == atoms.pop('params', [])
    assert msg.hostmask == atoms.pop('source', None)

    # Tags
    assert msg.tags == atoms.pop('tags', {})

    # Ensure that we tested with all the data provided
    assert not atoms


@pytest.mark.parametrize('test', load_irc_fixture('userhost-split'))
def test_identity_parsing(test):
    atoms = test['atoms']

    ident = Identity(test['source'])

    # Core identity
    assert ident.user == atoms.pop('user', '')
    assert ident.host == atoms.pop('host', '')
    assert ident.name == atoms.pop('nick', '')

    # Ensure that we tested with all the data provided
    assert not atoms
