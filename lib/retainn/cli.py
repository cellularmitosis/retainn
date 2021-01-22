"""Retain command-line interface functions."""

import sys
import os

from . import help
from . import db
from . import util
from . import prompt
from . import webapp
from . import curl
from . import py23


def run_help_command():
    """Execute the 'help' subcommand."""
    if len(sys.argv) < 3:
        help.print_help(sys.stdout)
        sys.exit(0)
    else:
        help_command = sys.argv[2]
        if help_command == 'review':
            help.print_review_help(sys.stdout)
            sys.exit(0)
        elif help_command == 'decks':
            help.print_decks_help(sys.stdout)
            sys.exit(0)
        elif help_command == 'import':
            help.print_import_help(sys.stdout)
            sys.exit(0)
        elif help_command == 'update-decks':
            help.print_update_decks_help(sys.stdout)
            sys.exit(0)
        elif help_command == 'update-deck':
            help.print_update_deck_help(sys.stdout)
            sys.exit(0)
        elif help_command == 'remove':
            help.print_remove_help(sys.stdout)
            sys.exit(0)
        elif help_command == 'serve':
            help.print_serve_help(sys.stdout)
            sys.exit(0)
        else:
            sys.stderr.write(
                "Error: no help for unknown command '%s'\n" % help_command
            )
            exe = os.path.basename(sys.argv[0])
            sys.stderr.write("Try '%s help'\n" % exe)
            sys.exit(1)


def run_review_command(db_conn, sql_templates):
    """Execute the 'review' command."""
    w = sys.stdout.write
    exe = os.path.basename(sys.argv[0])
    if db.select_count_card(db_conn, sql_templates) == 0:
        w("You have not imported any flashcard decks.\n")
        w("Try '%s help import'.\n" % exe)
        return
    
    session_start = db.make_tstamp()
    while True:
        card = db.select_next_card(db_conn, sql_templates, session_start)
        if card is None:
            w("You're done!  No more cards to review in this session.\n")
            w("Run %s again to start a new session.\n" % exe)
            sys.exit(0)
        else:
            w(
                '----------------------------------------------------------------\n'
            )
            w('Deck: %s\n' % card.deck_title)
            w('card_id: %s, score: %s\n\n' % (card.card_id, card.score))
            w(card.front)
            w('\n\n')
            prompt.prompt('--- (press any key to reveal back of card) ---')
            w('\n')
            w(card.back)
            w('\n\n')
            answer = prompt.prompt_Ynsq(
                "Were you able recall the answer (Yes, no, skip, quit)? [Y/n/s/q] "
            )
            if answer in ['y', 'n', 's']:
                if answer == 'y':
                    score = db.did_recall_card(db_conn, sql_templates, card.card_id)
                    w("Updating score: %s.\n\n" % score)
                elif answer == 'n':
                    score = db.did_not_recall_card(db_conn, sql_templates, card.card_id)
                    w("Updating score: %s.\n\n" % score)
                elif answer == 's':
                    db.skip_card(db_conn, sql_templates, card.card_id)
                    w("Skipping card (score: %s).\n\n" % card.score)
                continue
            elif answer == 'q':
                sys.exit(0)
            else:
                assert False, '(unreachable)'
            continue


def run_decks_command(db_conn, sql_templates):
    """Execute the 'decks' command."""
    w = sys.stdout.write
    deck_objs = db.select_decks(db_conn, sql_templates)
    if len(deck_objs) == 0:
        sys.stdout.write("You have not imported any flashcard decks.\n")
    else:
        sys.stdout.write("You have imported %s flashcard decks:\n" % len(deck_objs))
        for deck in deck_objs:
            w('\n')
            w("deck_id: %s\n" % deck.deck_id)
            w("title: %s\n" % deck.title)
            w("gist_url: %s\n" % deck.gist_url)
            continue
    sys.exit(0)


def run_import_command(db_conn, sql_templates):
    """Execute the 'import' command."""
    if len(sys.argv) < 3:
        help.print_import_help(sys.stderr)
        sys.exit(1)
    gist_url = sys.argv[2]
    deck_id = util.import_deck_url(db_conn, sql_templates, gist_url)
    sys.stdout.write("Imported deck_id: %s\n" % deck_id)
    sys.exit(0)


def run_update_decks_command(db_conn, sql_templates):
    """Execute the 'update-decks' command."""
    decks = db.select_decks(db_conn, sql_templates)
    w = sys.stdout.write
    if len(decks) == 0:
        w("You have not imported any flashcard decks.\n")
    else:
        for deck in decks:
            w("Checking deck %s '%s'... " % (deck.deck_id, deck.title))
            sys.stdout.flush()
            (markdown, new_etag) = curl.http_get_deck_if_needed(deck.gist_url, deck.etag)
            if markdown is None:
                w("up to date, skipping.\n")
                continue
            else:
                w("updating.\n")
                util.update_deck(db_conn, sql_templates, deck.deck_id, markdown, new_etag)
                continue
    sys.exit(0)


def run_update_deck_command(db_conn, sql_templates):
    """Execute the 'update-deck' command."""
    if len(sys.argv) < 3:
        help.print_import_help(sys.stderr)
        sys.exit(1)
    deck_id = int(sys.argv[2])
    assert False, 'Not implemented.'


def run_remove_command(db_conn, sql_templates):
    """Execute the 'remove' command."""
    assert False, 'Not implemented.'


def run_serve_command(db_conn, sql_templates):
    """Run the Retainn webapp locally."""
    import wsgiref.simple_server
    if len(sys.argv) == 2:
        host = 'localhost'
        port = 8080
    if len(sys.argv) == 3:
        # figure out if this is a host or a port.
        if py23.isnumeric(sys.argv[2]):
            host = 'localhost'
            port = int(sys.argv[2])
        else:
            host = sys.argv[2]
            port = 8080
    elif len(sys.argv) == 4:
        host = sys.argv[2]
        port = int(sys.argv[3])
    session_start = db.make_tstamp()
    application = webapp.make_application(db_conn, sql_templates, session_start)
    server = wsgiref.simple_server.make_server(host, port, application)
    sys.stdout.write("Starting webapp on http://%s:%s\n" % (host, port))
    server.serve_forever()
