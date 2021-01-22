"""Retainn database functions."""

import errno
import hashlib
import os
import sqlite3
import subprocess
import sys
import time

from . import py23


templates = None


# Thanks to https://stackoverflow.com/q/4984647
class Obj(dict):
    def __getattr__(self, attr):
        return self[attr]
    def __setattr__(self, attr, value):
        self[attr] = value


def make_tstamp():
    """Return the current epoch time in microseconds."""
    return int(time.time() * 1000000)


def read_file(fname):
    """Return the contents of a file."""
    with open(fname) as fd:
        contents = fd.read()
    return contents


# thanks to https://stackoverflow.com/a/600612
def mkdir_p(path):
    """Create a directory, creating any necessary parent directories."""
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def create_db(sql_templates_path, fname):
    """Create an Sqlite3 database, initialized with the retainn schema."""
    db_path = os.path.dirname(fname)
    if db_path not in ['', '.', './']:
        mkdir_p(db_path)
    schema = "%s/schema.sql" % sql_templates_path
    cmd = ['sqlite3', fname]
    stdin = open(schema)
    # FIXME: handle sqlite3 not being installed
    if sys.version_info[0] == 2:
        subprocess.check_call(cmd, stdin=stdin)
    else:
        subprocess.run(cmd, stdin=stdin, check=True)
    stdin.close()


def open_db(fname):
    """Connect to a Sqlite3 database file."""
    db_conn = sqlite3.connect(fname, isolation_level=None)
    return db_conn


def md5(s):
    """Return the md5 sum (as a hex string) of the given string."""
    if sys.version_info[0] == 2:
        return hashlib.md5(s.encode('utf-8')).hexdigest()
    else:
        if isinstance(s, str):
            return hashlib.md5(s.encode('utf-8')).hexdigest()
        else:
            return hashlib.md5(s).hexdigest()


def load_sql_template(fname):
    """Load an SQL template file from disk."""
    with open(fname) as fd:
        template = fd.read()
        # Unfortunately, an SQL comment could be considered a statement
        # by Python 2's sqlite3, which would then cause cursor.lastrowid to
        # be None!  This isn't an issue under Python 3.
        # As a work-around, strip the lines which start with '--'.
        if sys.version_info[0] == 2:
            lines = template.splitlines()
            lines = [line for line in lines if not line.startswith('--')]
            template = '\n'.join(lines)
    return template


def load_sql_templates(names=None, path='./sql'):
    """Load the SQL query templates from disk."""
    if names is None:
        names = [
            'insert_card',
            'insert_deck',
            'delete_deck',
            'select_decks',
            'select_card_by_id',
            'select_next_card',
            'select_count_card',
            'update_card_score_last_seen',
            'delete_cards_for_deck',
        ]
    templates = {}
    for name in names:
        fname = "%s/%s.sql" % (path, name)
        template = load_sql_template(fname)
        templates[name] = template
        continue
    return templates


def insert_deck(
    db_conn, sql_templates, gist_url, last_fetched, etag, hash, title, preamble
):
    """Insert a new deck into the database.
    Returns the deck_id of the inserted deck."""
    for var in [gist_url, hash, title, preamble]:
        assert py23.is_str(var)
    if etag is not None:
        assert py23.is_str(etag)
    assert py23.is_int(last_fetched)
    sql = sql_templates['insert_deck']
    params = {
        'gist_url': gist_url,
        'last_fetched': last_fetched,
        'etag': etag,
        'hash': hash,
        'title': title,
        'preamble': preamble
    }
    cursor = db_conn.cursor()
    cursor.execute(sql, params)
    deck_id = cursor.lastrowid
    assert deck_id is not None
    cursor.close()
    return deck_id


def delete_deck(db_conn, sql_templates, gist_url):
    """Delete any decks which match the given gist URL."""
    assert py23.is_str(gist_url)
    sql = sql_templates['delete_deck']
    cursor = db_conn.cursor()
    params = {'gist_url': gist_url}
    cursor.execute(sql, params)
    cursor.close()


def update_deck(
    db_conn, sql_templates, deck_id, last_fetched, etag, hash, title,
    preamble
):
    """Update an existing deck."""
    for var in [deck_id, last_fetched]:
        assert py23.is_int(var)
        continue
    for var in [hash, title, preamble]:
        assert py23.is_str(var)
        continue
    if etag is not None:
        assert py23.is_str(etag)
    sql = sql_templates['update_deck']
    params = {
        'deck_id': deck_id,
        'last_fetched': last_fetched,
        'etag': etag,
        'hash': hash,
        'title': title,
        'preamble': preamble
    }
    cursor = db_conn.cursor()
    cursor.execute(sql, params)
    cursor.close()


def select_decks(db_conn, sql_templates):
    """Select all of the decks.
    Returns a list of objects with keys: deck_id, gist_url, last_fetched, etag,
    hash, title, preamble."""
    sql = sql_templates['select_decks']
    cursor = db_conn.cursor()
    result = cursor.execute(sql)
    rows = result.fetchall()
    objs = []
    for row in rows:
        obj = Obj()
        obj.deck_id = row[0]
        obj.gist_url = row[1]
        obj.last_fetched = row[2]
        obj.etag = row[3]
        obj.hash = row[4]
        obj.title = row[5]
        obj.preamble = row[6]
        objs.append(obj)
        continue
    cursor.close()
    return objs


def make_card_hash(front, back):
    """Create a hash of a card which can be used to detect content changes."""
    hash = "%s.%s" % (md5(front), md5(back))
    return hash


def insert_card(
    db_conn, sql_templates, front, back, deck_id, last_seen=None, score=0
):
    """Insert a new card into the database.
    Returns the card_id of the inserted card."""
    for var in [front, back]:
        assert py23.is_str(var)
        continue
    for var in [deck_id, score]:
        assert py23.is_int(var)
        continue
    if last_seen is not None:
        assert py23.is_int(last_seen)
    sql = sql_templates['insert_card']
    hash = make_card_hash(front, back)
    params = {
        'score': score,
        'last_seen': last_seen,
        'front': front,
        'back': back,
        'hash': hash,
        'deck_id': deck_id
    }
    cursor = db_conn.cursor()
    cursor.execute(sql, params)
    card_id = cursor.lastrowid
    assert card_id is not None
    cursor.close()
    return card_id


def select_count_card(db_conn, sql_templates):
    """Return the number of cards."""
    sql = sql_templates['select_count_card']
    cursor = db_conn.cursor()
    result = cursor.execute(sql)
    (count,) = result.fetchone()
    cursor.close()
    return int(count)


def select_next_card(db_conn, sql_templates, session_start):
    """Select the best next card to show the user.
    Returns an object with keys: card_id, score, last_seen, front, back,
    deck_id, deck_title."""
    assert py23.is_int(session_start)
    sql = sql_templates['select_next_card']
    params = {
        'session_start': session_start
    }
    cursor = db_conn.cursor()
    results = cursor.execute(sql, params)
    row = results.fetchone()
    cursor.close()
    if row is None:
        return None
    else:
        obj = Obj()
        obj.card_id = row[0]
        obj.score = row[1]
        obj.front = row[2]
        obj.back = row[3]
        obj.deck_id = row[4]
        obj.deck_title = row[5]
        return obj


def select_card(db_conn, sql_templates, card_id):
    assert py23.is_int(card_id)
    sql = sql_templates['select_card_by_id']
    params = {
        'card_id': card_id
    }
    cursor = db_conn.cursor()
    results = cursor.execute(sql, params)
    row = results.fetchone()
    cursor.close()
    assert row is not None
    obj = Obj()
    obj.card_id = row[0]
    obj.score = row[1]
    obj.front = row[2]
    obj.back = row[3]
    obj.deck_id = row[4]
    obj.deck_title = row[5]
    return obj


def select_card_hashes_by_deck_id(db_conn, sql_templates, deck_id):
    assert py23.is_int(deck_id)
    sql = sql_templates['select_card_hashes_by_deck_id']
    params = {
        'deck_id': deck_id
    }
    cursor = db_conn.cursor()
    results = cursor.execute(sql, params)
    row_tuples = results.fetchall()
    hashes = [tup[0] for tup in row_tuples]
    cursor.close()
    return hashes


def update_card_score_last_seen(
    db_conn, sql_templates, card_id, score, last_seen
):
    """Update the card's score and last_seen values.
    No return value."""
    for var in [card_id, score, last_seen]:
        assert py23.is_int(var)
        continue
    sql = sql_templates['update_card_score_last_seen']
    params = {
        'card_id': card_id,
        'score': score,
        'last_seen': last_seen
    }
    cursor = db_conn.cursor()
    result = cursor.execute(sql, params)
    cursor.close()


def did_recall_card(db_conn, sql_templates, card_id):
    card = select_card(db_conn, sql_templates, card_id)
    if card.score < 1:
        score = 1
    else:
        score = card.score + 1
    now = make_tstamp()
    last_seen = now
    update_card_score_last_seen(
        db_conn, sql_templates, card_id, score, last_seen
    )
    return score


def did_not_recall_card(db_conn, sql_templates, card_id):
    card = select_card(db_conn, sql_templates, card_id)
    if card.score > 1:
        score = -1
    else:
        score = card.score - 1
    now = make_tstamp()
    last_seen = now
    update_card_score_last_seen(
        db_conn, sql_templates, card_id, score, last_seen
    )
    return score


def skip_card(db_conn, sql_templates, card_id):
    card = select_card(db_conn, sql_templates, card_id)
    score = card.score
    now = make_tstamp()
    last_seen = now
    update_card_score_last_seen(
        db_conn, sql_templates, card_id, score, last_seen
    )


def delete_cards_for_deck(db_conn, sql_templates, deck_id):
    """Delete all cards matching the given deck_id from the database."""
    assert py23.is_int(deck_id)
    sql = sql_templates['delete_cards_for_deck']
    params = {'deck_id': deck_id}
    cursor = db_conn.cursor()
    cursor.execute(sql, params)
    cursor.close()


def delete_cards_by_hash(db_conn, sql_templates, deck_id, card_hashes):
    """Delete the cards from a deck matching the given set of hashes."""
    assert py23.is_int(deck_id)
    assert isinstance(card_hashes, set)
    assert len(card_hashes) > 0
    sql = sql_templates['delete_cards_by_hash']
    sql = sql_replace_where_in(sql, len(card_hashes))
    params = [deck_id] + list(card_hashes)
    cursor = db_conn.cursor()
    cursor.execute(sql, params)
    cursor.close()


def sql_replace_where_in(sql, q_count):
    """Support 'WHERE IN' SQL templates.  Replace the first occurence of the
    string '(?...?)' with some number of qmarks, e.g. '(?,?,?)'."""
    qs = ','.join('?' * q_count)
    sql2 = sql.replace('?...?', qs)
    return sql2
