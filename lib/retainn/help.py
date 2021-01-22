"""Retainn help messages."""

import sys
import os


def print_help(fd):
    """Print the usage string to the file descriptor."""
    w = fd.write
    exe = os.path.basename(sys.argv[0])
    w("%s: a spaced-repetition flashcard system.\n" % exe)
    w("See https://retainn.org\n")
    w("\n")
    w("Usage:\n")
    w("  %s help [command]\n" % exe)
    w("  %s review\n" % exe)
    w("  %s decks\n" % exe)
    w("  %s import <gist URL>\n" % exe)
    w("  %s update-decks\n" % exe)
    w("  %s update-deck <deck id>\n" % exe)
    w("  %s remove <deck_id | gist URL>\n" % exe)
    w("  %s serve [host] [port]\n" % exe)


def print_review_help(fd):
    """Print the 'review' command usage to the file descriptor."""
    w = fd.write
    w("Command 'review':\n")
    w("  Start a flashcard review session.\n")
    w("\n")
    exe = os.path.basename(sys.argv[0])
    w("Usage:\n")
    w("  %s review\n" % exe)


def print_decks_help(fd):
    """Print the 'decks' command usage to the file descriptor."""
    w = fd.write
    w("Command 'decks':\n")
    w("  List the decks which have been imported.\n")
    w("\n")
    exe = os.path.basename(sys.argv[0])
    w("Usage:\n")
    w("  %s decks\n" % exe)


def print_import_help(fd):
    """Print the 'import' command usage to the file descriptor."""
    w = fd.write
    w("Command 'import':\n")
    w("  Download and import a flashcard deck from a github gist URL.\n")
    w("\n")
    exe = os.path.basename(sys.argv[0])
    w("Usage:\n")
    w("  %s import https://gist.github.com/...\n" % exe)


def print_update_decks_help(fd):
    """Print the 'update-decks' command usage to the file descriptor."""
    w = fd.write
    w("Command 'update-decks':\n")
    w("  Check if any decks are out-of-date (using etags)")
    w(" and pull in the changes as needed.\n")
    w("\n")
    exe = os.path.basename(sys.argv[0])
    w("Usage:\n")
    w("  %s update-decks\n" % exe)


def print_update_deck_help(fd):
    """Print the 'update-deck' command usage to the file descriptor."""
    w = fd.write
    w("Command 'update-deck':\n")
    w("  Update the specified deck (disregarding etags).\n")
    w("\n")
    exe = os.path.basename(sys.argv[0])
    w("Usage:\n")
    w("  %s update-deck 3\n" % exe)


def print_remove_help(fd):
    """Print the 'remove' command usage to the file descriptor."""
    assert False, 'Not implemented.'


def print_serve_help(fd):
    """Print the 'serve' command usage to the file descriptor."""
    w = fd.write
    w("Command 'serve':\n")
    w("  Run the Retainn webapp server.\n")
    w("\n")
    exe = os.path.basename(sys.argv[0])
    w("Usage:\n")
    w("  %s serve [host] [port]\n" % exe)
    w("\n")
    w("Defaults are localhost and port 8080.\n")
    w("\n")
    w("Examples:\n")
    w("  %s serve\n" % exe)
    w("  %s serve 8081\n" % exe)
    w("  %s serve 0.0.0.0\n" % exe)
    w("  %s serve 0.0.0.0 8081\n" % exe)
