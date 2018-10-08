import pytest
import yaml

from seabird.irc import Message, Identity


@pytest.fixture
def irc_fixture_loader():
    def func(fname):
        with open(f'irc-parser-tests/tests/{fname}.yaml') as f:
            return yaml.load(f)['tests']

    return func


def test_message_parsing(irc_fixture_loader):
    tests = irc_fixture_loader('msg-split')
    assert tests

    for test in tests:
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


def test_identity_parsing(irc_fixture_loader):
    tests = irc_fixture_loader('userhost-split')
    assert tests

    for test in tests:
        atoms = test['atoms']

        ident = Identity(test['source'])

        # Core identity
        assert ident.user == atoms.pop('user', '')
        assert ident.host == atoms.pop('host', '')
        assert ident.name == atoms.pop('nick', '')

        # Ensure that we tested with all the data provided
        assert not atoms
