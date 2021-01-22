"""Retainn utility functions."""

from . import curl
from . import parse
from . import db


def import_deck_url(db_conn, sql_templates, gist_url):
    """Download a deck and insert it into the database.
    Returns the deck_id of the newly inserted deck."""
    (markdown, etag) = curl.http_get_deck_and_etag(gist_url)
    return import_deck_md(db_conn, sql_templates, gist_url, etag, markdown)


def import_deck_md(db_conn, sql_templates, gist_url, etag, markdown):
    """Insert the deck into the database.
    Returns the deck_id of the newly inserted deck."""
    last_fetched = db.make_tstamp()
    hash = db.md5(markdown)
    tokens = parse.lex_deck(markdown)
    (deck_ast, _) = parse.parse_deck(tokens)
    assert deck_ast is not None
    preamble_md = deck_ast.preamble.text
    title = parse.extract_title(preamble_md)
    db.delete_deck(db_conn, sql_templates, gist_url)
    deck_id = db.insert_deck(
        db_conn, sql_templates, gist_url, last_fetched, etag, hash, title,
        preamble_md
    )
    assert deck_id is not None
    # FIXME should we alert or prompt the user about this?
    db.delete_cards_for_deck(db_conn, sql_templates, deck_id)
    for card_ast in deck_ast.cards:
        front = card_ast.front_text
        back = card_ast.back_text
        card_id = db.insert_card(db_conn, sql_templates, front, back, deck_id)
        assert card_id is not None
        continue
    return deck_id


def update_deck(db_conn, sql_templates, deck_id, markdown, etag):
    # update the deck
    last_fetched = db.make_tstamp()
    deck_hash = db.md5(markdown)
    tokens = parse.lex_deck(markdown)
    (deck_ast, _) = parse.parse_deck(tokens)
    preamble_md = deck_ast.preamble.text
    title = parse.extract_title(preamble_md)
    db.update_deck(
        db_conn, sql_templates, deck_id, last_fetched, etag, deck_hash, title,
        preamble_md
    )

    # then update the individual cards
    old_card_hashes = set(
        db.select_card_hashes_by_deck_id(db_conn, sql_templates, deck_id)
    )
    new_card_hashes = set()
    for card_ast in deck_ast.cards:
        front = card_ast.front_text
        back = card_ast.back_text
        card_hash = db.make_card_hash(front, back)
        new_card_hashes.add(card_hash)
        continue

    to_be_removed = old_card_hashes.difference(new_card_hashes)
    db.delete_cards_by_hash(db_conn, sql_templates, deck_id, to_be_removed)

    to_be_inserted = new_card_hashes.difference(old_card_hashes)
    for card_ast in deck_ast.cards:
        front = card_ast.front_text
        back = card_ast.back_text
        card_hash = db.make_card_hash(front, back)
        if card_hash in to_be_inserted:
            card_id = db.insert_card(db_conn, sql_templates, front, back, deck_id)
            assert card_id is not None
        continue
    return
