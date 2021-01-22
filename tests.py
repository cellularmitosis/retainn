"""Retainn unit test functions."""

from __future__ import print_function

import sqlite3
import sys

sys.path.insert(0, "./lib")
from retainn import db
from retainn import curl
from retainn import util
from retainn import py23


def make_memory_db():
    """Create an in-memory databse with our schema."""
    # 'isolation_level=None' means autocommit mode.
    db_conn = db.open_db(':memory:')
    schema = db.read_file('lib/retainn/sql/schema.sql')
    cursor = db_conn.cursor()
    cursor.executescript(schema)
    cursor.close()
    return db_conn


def test_md5():
    hash = db.md5('Hello, world!')
    assert hash == '6cd3556deb0da54bca060b4c39479839'


def test_get_deck():
    url = "https://gist.github.com/cellularmitosis/fe539a6529d3787d94517f94def1bc4d"
    etag1 = None
    (markdown, etag2) = curl.http_get_deck_if_needed(url, etag1)
    assert etag2 is not None, "etag2 should not be None"
    (markdown, etag3) = curl.http_get_deck_if_needed(url, etag2)
    assert etag3 is None, "etag3 should be None. etag1: %s, etag2: %s, etag3: %s" % (etag1, etag2, etag3)


def test_insert_deck():
    db_conn = make_memory_db()
    sql_templates = db.load_sql_templates(['insert_deck'], path='lib/retainn/sql')
    gist_url = 'url'
    last_fetched = 1
    etag = 'etag'
    hash = 'hash'
    title = 'title'
    preamble = 'preamble'
    deck_id = db.insert_deck(
        db_conn, sql_templates, gist_url, last_fetched, etag, hash, title,
        preamble
    )
    assert py23.is_int(deck_id), "deck_id: %s" % deck_id
    db_conn.close()


def test_insert_card():
    db_conn = make_memory_db()
    sql_templates = db.load_sql_templates(['insert_card'], path='lib/retainn/sql')
    front = 'front'
    back = 'back'
    deck_id = 1
    last_seen = 1
    card_id = db.insert_card(
        db_conn, sql_templates, front, back, deck_id, last_seen
    )
    assert py23.is_int(card_id), "card_id: %s" % card_id
    db_conn.close()


def test_select_next_card():
    db_conn = make_memory_db()
    sql_templates = db.load_sql_templates(['select_next_card'], path='lib/retainn/sql')
    cursor = db_conn.cursor()
    cursor.execute("""
    INSERT INTO deck (gist_url, last_fetched, etag, hash, title, preamble)
    VALUES ('http://', 1, 'etag', 'hash', 'title', 'preamble');
    """)
    deck_id = cursor.lastrowid
    assert deck_id is not None
    cursor.execute("""
    INSERT INTO card (score, last_seen, front, back, hash, deck_id)
    VALUES (1, 1, 'front', 'back', 'hash', :deck_id);
    """, {'deck_id': deck_id})
    card_id = cursor.lastrowid
    assert card_id is not None
    cursor.close()
    session_start = 2
    obj = db.select_next_card(db_conn, sql_templates, session_start)
    assert obj.card_id == card_id
    db_conn.close()


def test_update_card_score_last_seen():
    db_conn = make_memory_db()
    sql_templates = db.load_sql_templates(
        ['update_card_score_last_seen'],
        path='lib/retainn/sql'
    )
    cursor = db_conn.cursor()
    cursor.execute("""
    INSERT INTO deck (gist_url, last_fetched, etag, hash, title, preamble)
    VALUES ('http://', 1, 'etag', 'hash', 'title', 'preamble');
    """)
    deck_id = cursor.lastrowid
    assert deck_id is not None
    cursor.execute("""
    INSERT INTO card (score, last_seen, front, back, hash, deck_id)
    VALUES (1, 1, 'front', 'back', 'hash', :deck_id);
    """, {'deck_id': deck_id})
    card_id = cursor.lastrowid
    assert card_id is not None
    score = 2
    last_seen = 3
    db.update_card_score_last_seen(db_conn, sql_templates, card_id, score, last_seen)
    result = cursor.execute(
        "SELECT score, last_seen FROM card WHERE card_id = :card_id LIMIT 1",
        {'card_id': card_id}
    )
    (new_score, new_last_seen) = result.fetchone()
    assert new_score == score
    assert new_last_seen == last_seen
    cursor.close()
    db_conn.close()


def test_import_deck_url():
    db_conn = make_memory_db()
    sql_templates = db.load_sql_templates(
        ['insert_deck', 'delete_deck', 'insert_card', 'delete_cards_for_deck'],
        path='lib/retainn/sql'
    )
    gist_url = "https://gist.github.com/cellularmitosis/fe539a6529d3787d94517f94def1bc4d"
    deck_id = util.import_deck_url(db_conn, sql_templates, gist_url)
    assert deck_id is not None
    db_conn.close()


def test_update_deck():
    db_conn = make_memory_db()
    sql_templates = db.load_sql_templates(
        ['insert_deck', 'delete_deck', 'insert_card', 'delete_cards_for_deck',
        'select_decks', 'update_deck', 'select_card_hashes_by_deck_id',
        'delete_cards_by_hash'],
        path='lib/retainn/sql'
    )
    deck_md_1 = b"""format: md1
# Some Deck

A deck with some cards

---

This is the front of a card.

%

This the back of a card.

---

This is the front of card 2.

%

This is the back of card 2.

---
"""

    deck_md_2 = b"""format: md1
# Some Deck

A deck with some cards

---

UPDATED This is the front of a card.

%

This the back of a card.

---

This is the front of card 2.

%

This is the back of card 2.

---
"""
    gist_url = "http://example.com"
    etag = None
    deck_id = util.import_deck_md(db_conn, sql_templates, gist_url, etag, deck_md_1)
    assert deck_id is not None
    decks_before = db.select_decks(db_conn, sql_templates)

    result = db_conn.execute("SELECT c.front FROM card c WHERE c.deck_id = ?", [deck_id])
    cards_before = [tup[0] for tup in result.fetchall()]
    assert len(cards_before) == 2
    assert cards_before[0] == b"This is the front of a card."

    util.update_deck(db_conn, sql_templates, deck_id, deck_md_2, etag)
    decks_after = db.select_decks(db_conn, sql_templates)

    assert len(decks_after) == 1
    assert len(decks_before) == len(decks_after)

    dbefore = decks_before[0]
    dafter = decks_after[0]
    assert dbefore.deck_id == dafter.deck_id

    result = db_conn.execute("SELECT c.front FROM card c WHERE c.deck_id = ?", [deck_id])
    cards_after = [tup[0] for tup in result.fetchall()]
    assert len(cards_after) == 2
    assert cards_after[1] == b"UPDATED This is the front of a card."

    db_conn.close()


if __name__ == "__main__":
    test_md5()
    # test_get_deck()
    test_select_next_card()
    test_update_card_score_last_seen()
    test_insert_deck()
    test_insert_card()
    test_import_deck_url()
    test_update_deck()
