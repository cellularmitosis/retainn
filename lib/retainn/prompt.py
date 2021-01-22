"""Retainn user-prompting functions."""

import sys
import os
import string


def is_printable(ch):
    """Return whether ch is printable (excluding whitespace)."""
    return ch in string.digits + string.ascii_letters + string.punctuation


# thanks to https://stackoverflow.com/a/34956791
# hmm, this doesn't seem to work on win7 / msys2.
def wait_key():
    """Wait for a key press on the console and return it."""
    result = None
    if os.name == 'nt':
        import msvcrt
        result = msvcrt.getch()
    else:
        import termios
        fd = sys.stdin.fileno()

        oldterm = termios.tcgetattr(fd)
        newattr = termios.tcgetattr(fd)
        newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
        termios.tcsetattr(fd, termios.TCSANOW, newattr)

        try:
            result = sys.stdin.read(1)
        except IOError:
            pass
        finally:
            termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)

    return result


def prompt(msg):
    """Prompt the user and wait for them to hit any key."""
    sys.stdout.write(msg)
    sys.stdout.flush()
    key = wait_key()
    sys.stdout.write('\n')
    return key


def prompt_Ynq(msg):
    """Ask the user a yes/no/quit question (default answer: yes)."""
    while True:
        sys.stdout.write(msg)
        sys.stdout.flush()
        answer = wait_key()
        if is_printable(answer):
            sys.stdout.write("%s" % answer)
        sys.stdout.write('\n')
        answer = answer.lower()
        if answer in ['\n', 'y']:
            return 'y'
        elif answer in ['n', 'q']:
            return answer
        else:
            sys.stdout.write(
                "Please answer 'y', 'n', or 'q' (or press enter for default 'y').\n"
            )
            continue


def prompt_Ynsq(msg):
    """Ask the user a yes/no/skip/quit question (default answer: yes)."""
    while True:
        sys.stdout.write(msg)
        sys.stdout.flush()
        answer = wait_key()
        if is_printable(answer):
            sys.stdout.write("%s" % answer)
        sys.stdout.write('\n')
        answer = answer.lower()
        if answer in ['\n', 'y']:
            return 'y'
        elif answer in ['n', 's', 'q']:
            return answer
        else:
            sys.stdout.write(
                "Please answer 'y', 'n', 's', or 'q' (or press enter for default 'y').\n"
            )
            continue
