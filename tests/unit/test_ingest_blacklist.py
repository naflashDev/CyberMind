import pytest
from app.services.documents.ingest import is_blacklisted_filename


def test_blacklisted_names():
    assert is_blacklisted_filename('delta.json')
    assert is_blacklisted_filename('Delta.json')
    assert is_blacklisted_filename('deltalog.json')
    assert is_blacklisted_filename('README.md')
    assert is_blacklisted_filename('.gitignore')


def test_not_blacklisted():
    assert not is_blacklisted_filename('notes.txt')
    assert not is_blacklisted_filename('document.pdf')
    assert not is_blacklisted_filename(None)
