"""Retainn markdown parsing functions."""

import re


# Thanks to https://stackoverflow.com/q/4984647
class Obj(dict):
    def __getattr__(self, attr):
        return self[attr]
    def __setattr__(self, attr, value):
        self[attr] = value

# TODO refactor to split these up, into '\n\n', '---', and '%'


def lex_deck(text):
    """Lex the markdown text into tokens.
    Returns an array of tokens (objects with keys: type, text).
    On failure, returns an error (object with keys: type, message)."""
    pattern_table = [
        ('TOK_CODE',  b'\n```'),
        ('TOK_FRONT', b'\n\n---\n\n'),
        ('TOK_BACK',  b'\n\n%\n\n'),
        ('TOK_LAST',  b'\n\n---\n'),
        ('TOK_OTHER', b'[\s\S]'),
    ]

    regex_table = []
    for label, pattern in pattern_table:
        regex = re.compile(pattern)
        pair = (label, regex)
        regex_table.append(pair)
        continue

    tokens = []
    index = 0
    input_len = len(text)
    while index < input_len:
        for label, regex in regex_table:
            match = regex.match(text, index)
            if match:
                matched_text = match.group()
                token = Obj()
                token.type = label
                token.text = matched_text
                tokens.append(token)
                index += len(matched_text)
                break
            else:
                continue
        else:
            context = text[index:index+16]
            error = Obj()
            error.type = 'ERROR'
            error.message = "Couldn't match any token (index %s, context: )" \
                % (index, context)
            return error
        continue
    return tokens


def parse_code(tokens, index):
    """Parse a code AST node.
    Returns (AST node, next token index).
    AST node is an object with keys: type, text.
    Returns (None, original index) on failure."""
    failure = (None, index)
    code_text = ''
    saved_tokens = tokens[index:]  # DEBUG

    token = tokens[index]
    assert token.type == 'TOK_CODE'
    code_text += token.text
    index += 1

    did_find_closing = False
    while index < len(tokens):
        token = tokens[index]
        code_text += token.text
        index += 1
        if token.type == 'TOK_CODE':
            did_find_closing = True
            break
        else:
            continue
    if did_find_closing == False:
        return failure

    ast = Obj()
    ast.type = 'AST_CODE'
    ast.text = code_text
    return (ast, index)


def parse_preamble(tokens, index):
    """Parse a preamble AST node.
    Returns (AST node, next token index).
    AST node is an object with keys: type, text."""
    failure = (None, index)
    preamble_text = b''
    while index < len(tokens):
        token = tokens[index]
        if token.type == 'TOK_CODE':
            ast, index = parse_code(tokens, index)
            if ast is None:
                return failure
            preamble_text += ast.text
            continue
        elif token.type == 'TOK_FRONT':
            # this signals the start of the first card.
            break
        else:
            preamble_text += token.text
            index += 1
            continue
    ast = Obj()
    ast.type = 'AST_PREAMBLE'
    ast.text = preamble_text
    return (ast, index)


def flatten_preamble(ast):
    """Flatten a preamble AST node into a string."""
    assert ast.type == 'AST_PREAMBLE'
    return ast.text


def extract_title(preamble_md):
    """Extract the title from preamble markdown.
    Returns None on failure."""
    # title regex: some number of hashes followed by a non-hash.
    regex = re.compile(b'^#+[^#]\s*(.*)$')
    for line in preamble_md.splitlines():
        m = regex.match(line)
        if m:
            title = m.group(1)
            return title
        else:
            continue
    return None


def parse_card(tokens, index):
    """Parse a card AST node.
    Returns (AST node, next token index).
    AST node is an object with keys: type, front_demarcator_token, front_text,
    back_demarcator_token, back_text.
    Returns (None, original index) on failure."""
    failure = (None, index)
    ast = None
    front_demarcator_token = tokens[index]
    assert front_demarcator_token.type == 'TOK_FRONT'
    index += 1

    front_text = b''
    back_demarcator_token = None
    while index < len(tokens):
        token = tokens[index]
        index += 1
        if token.type == 'TOK_BACK':
            back_demarcator_token = token
            break
        else:
            front_text += token.text
            continue
    if back_demarcator_token is None:
        return failure

    back_text = b''
    while index < len(tokens):
        token = tokens[index]
        if token.type in ['TOK_FRONT', 'TOK_LAST']:
            break
        else:
            back_text += token.text
            index += 1
            continue

    ast = Obj()
    ast.type = 'AST_CARD'
    ast.front_demarcator_token = front_demarcator_token
    ast.front_text = front_text
    ast.back_demarcator_token = back_demarcator_token
    ast.back_text = back_text
    return (ast, index)


def flatten_card(ast):
    """Flatten a card AST node into a string."""
    string = ast.front_demarcator_token.text \
        + ast.front_text \
        + ast.back_demarcator_token.text \
        + ast.back_text
    return string


def parse_deck(tokens, index=0):
    """Parse a deck AST node.
    Returns (AST node, next token index).
    AST node is an object with keys: type, preamble, cards, last_token.
    Returns (None, original index) on failure."""
    failure = (None, index)
    preamble, index = parse_preamble(tokens, index)
    if preamble is None:
        return failure

    card_nodes = []
    last_token = None
    while index < len(tokens):
        card_node, index = parse_card(tokens, index)
        if card_node is None:
            return failure
        else:
            card_nodes.append(card_node)
        
        next_token = tokens[index]
        if next_token.type == 'TOK_LAST':
            last_token = next_token
            index += 1
            break
        else:
            continue
    if last_token is None:
        return failure

    ast = Obj()
    ast.type = 'AST_DECK'
    ast.preamble = preamble
    ast.cards = card_nodes
    ast.last_token = last_token
    return (ast, index)


def flatten_deck(ast):
    """Flatten a deck AST into a string."""
    string = flatten_preamble(ast.preamble)
    for card in ast.cards:
        string += flatten_card(card)
        continue
    string += ast.last_token.text
    return string


def write_deck_to_disk(ast, outdir_path):
    """Write each card in the deck to disk as individual files."""
    assert ast.type == 'AST_DECK'
    text = flatten_preamble(ast.preamble) + '\n'  # FIXME refactor out this cheat
    outfile = "%s/preamble.md" % outdir_path
    with open(outfile, "w+") as fd:
        fd.write(text)
    for i, card in enumerate(deck.cards):
        front_text = card.front_text + '\n'  # FIXME refactor out this cheat
        outfile = "%s/%d-front.md" % (outdir_path, i)
        with open(outfile, "w+") as fd:
            fd.write(front_text)
        back_text = card.back_text + '\n'  # FIXME refactor out this cheat
        outfile = "%s/%d-back.md" % (outdir_path, i)
        with open(outfile, "w+") as fd:
            fd.write(back_text)
        continue
