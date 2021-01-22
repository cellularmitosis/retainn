"""The local Retainn WSGI webapp."""

import re

try:
    # Python 3
    from io import StringIO
except ImportError:
    # Python 2
    from StringIO import StringIO

from . import db
from . import util
from .vendored import markdown2


# Enable some markdown2 "extra" features.
# See https://github.com/trentm/python-markdown2/wiki/Extras
md2html = markdown2.Markdown(extras = [
    "cuddled-lists",
    "fenced-code-blocks",
    "strike",
    "tables"
]).convert


# CSS for pygments syntax highlighting.
css = """
.codehilite .hll { background-color: #ffffcc }
.codehilite  { background: #f8f8f8; }
.codehilite .c { color: #408080; font-style: italic } /* Comment */
.codehilite .err { border: 1px solid #FF0000 } /* Error */
.codehilite .k { color: #008000; font-weight: bold } /* Keyword */
.codehilite .o { color: #666666 } /* Operator */
.codehilite .ch { color: #408080; font-style: italic } /* Comment.Hashbang */
.codehilite .cm { color: #408080; font-style: italic } /* Comment.Multiline */
.codehilite .cp { color: #BC7A00 } /* Comment.Preproc */
.codehilite .cpf { color: #408080; font-style: italic } /* Comment.PreprocFile */
.codehilite .c1 { color: #408080; font-style: italic } /* Comment.Single */
.codehilite .cs { color: #408080; font-style: italic } /* Comment.Special */
.codehilite .gd { color: #A00000 } /* Generic.Deleted */
.codehilite .ge { font-style: italic } /* Generic.Emph */
.codehilite .gr { color: #FF0000 } /* Generic.Error */
.codehilite .gh { color: #000080; font-weight: bold } /* Generic.Heading */
.codehilite .gi { color: #00A000 } /* Generic.Inserted */
.codehilite .go { color: #888888 } /* Generic.Output */
.codehilite .gp { color: #000080; font-weight: bold } /* Generic.Prompt */
.codehilite .gs { font-weight: bold } /* Generic.Strong */
.codehilite .gu { color: #800080; font-weight: bold } /* Generic.Subheading */
.codehilite .gt { color: #0044DD } /* Generic.Traceback */
.codehilite .kc { color: #008000; font-weight: bold } /* Keyword.Constant */
.codehilite .kd { color: #008000; font-weight: bold } /* Keyword.Declaration */
.codehilite .kn { color: #008000; font-weight: bold } /* Keyword.Namespace */
.codehilite .kp { color: #008000 } /* Keyword.Pseudo */
.codehilite .kr { color: #008000; font-weight: bold } /* Keyword.Reserved */
.codehilite .kt { color: #B00040 } /* Keyword.Type */
.codehilite .m { color: #666666 } /* Literal.Number */
.codehilite .s { color: #BA2121 } /* Literal.String */
.codehilite .na { color: #7D9029 } /* Name.Attribute */
.codehilite .nb { color: #008000 } /* Name.Builtin */
.codehilite .nc { color: #0000FF; font-weight: bold } /* Name.Class */
.codehilite .no { color: #880000 } /* Name.Constant */
.codehilite .nd { color: #AA22FF } /* Name.Decorator */
.codehilite .ni { color: #999999; font-weight: bold } /* Name.Entity */
.codehilite .ne { color: #D2413A; font-weight: bold } /* Name.Exception */
.codehilite .nf { color: #0000FF } /* Name.Function */
.codehilite .nl { color: #A0A000 } /* Name.Label */
.codehilite .nn { color: #0000FF; font-weight: bold } /* Name.Namespace */
.codehilite .nt { color: #008000; font-weight: bold } /* Name.Tag */
.codehilite .nv { color: #19177C } /* Name.Variable */
.codehilite .ow { color: #AA22FF; font-weight: bold } /* Operator.Word */
.codehilite .w { color: #bbbbbb } /* Text.Whitespace */
.codehilite .mb { color: #666666 } /* Literal.Number.Bin */
.codehilite .mf { color: #666666 } /* Literal.Number.Float */
.codehilite .mh { color: #666666 } /* Literal.Number.Hex */
.codehilite .mi { color: #666666 } /* Literal.Number.Integer */
.codehilite .mo { color: #666666 } /* Literal.Number.Oct */
.codehilite .sa { color: #BA2121 } /* Literal.String.Affix */
.codehilite .sb { color: #BA2121 } /* Literal.String.Backtick */
.codehilite .sc { color: #BA2121 } /* Literal.String.Char */
.codehilite .dl { color: #BA2121 } /* Literal.String.Delimiter */
.codehilite .sd { color: #BA2121; font-style: italic } /* Literal.String.Doc */
.codehilite .s2 { color: #BA2121 } /* Literal.String.Double */
.codehilite .se { color: #BB6622; font-weight: bold } /* Literal.String.Escape */
.codehilite .sh { color: #BA2121 } /* Literal.String.Heredoc */
.codehilite .si { color: #BB6688; font-weight: bold } /* Literal.String.Interpol */
.codehilite .sx { color: #008000 } /* Literal.String.Other */
.codehilite .sr { color: #BB6688 } /* Literal.String.Regex */
.codehilite .s1 { color: #BA2121 } /* Literal.String.Single */
.codehilite .ss { color: #19177C } /* Literal.String.Symbol */
.codehilite .bp { color: #008000 } /* Name.Builtin.Pseudo */
.codehilite .fm { color: #0000FF } /* Name.Function.Magic */
.codehilite .vc { color: #19177C } /* Name.Variable.Class */
.codehilite .vg { color: #19177C } /* Name.Variable.Global */
.codehilite .vi { color: #19177C } /* Name.Variable.Instance */
.codehilite .vm { color: #19177C } /* Name.Variable.Magic */
.codehilite .il { color: #666666 } /* Literal.Number.Integer.Long */
"""


# Thanks to https://stackoverflow.com/q/4984647
class Obj(dict):
    def __getattr__(self, attr):
        return self[attr]
    def __setattr__(self, attr, value):
        self[attr] = value


def POST_did_recall(request, path_match, db_conn, sql_templates, session):
    """A user POSTs to this endpoint to indicate that they were able to recall
    a card."""
    card_id = int(path_match.group(1))
    response = Obj()
    db.did_recall_card(db_conn, sql_templates, card_id)
    response.status = '302 Found'
    response.headers = [
        ('Location', '/')
    ]
    return response


def POST_did_not_recall(request, path_match, db_conn, sql_templates, session):
    """A user POSTs to this endpoint to indicate that they were NOT able to
    recall a card."""
    card_id = int(path_match.group(1))
    response = Obj()
    db.did_not_recall_card(db_conn, sql_templates, card_id)
    response.status = '302 Found'
    response.headers = [
        ('Location', '/')
    ]
    return response


def POST_skip(request, path_match, db_conn, sql_templates, session):
    """A user POSTs to this endpoint to skip a card."""
    card_id = int(path_match.group(1))
    response = Obj()
    db.skip_card(db_conn, sql_templates, card_id)
    response.status = '302 Found'
    response.headers = [
        ('Location', '/')
    ]
    return response


def GET_card(request, path_match, db_conn, sql_templates, session):
    response = Obj()
    buf = StringIO()
    bw = buf.write
    if db.select_count_card(db_conn, sql_templates) == 0:
        bw(u"You have not imported any flashcard decks.\n")
    else:
        card_id = int(path_match.group(1))
        card = db.select_card(db_conn, sql_templates, card_id)
        bw(u"# Deck: %s\n" % card.deck_title)
        bw(u"- card_id: %s, score: %s\n" % (card.card_id, card.score))
        bw(u"\n\n----\n\n")
        bw(u"\n## Front of card:\n\n")
        bw(card.front)
        bw(u"\n\n----\n\n")
        bw(u"\n## Back of card:\n\n")
        bw(card.back)
        bw(u"\n\n----\n\n")
        bw(u"\n\nWere you able to recall the answer?\n\n")
        bw(u"<form method=\"POST\" action=\"/cards/%s/did-recall\">\n <button>Yes</button>\n</form>\n\n" % card_id)
        bw(u"<form method=\"POST\" action=\"/cards/%s/did-not-recall\">\n <button>No</button>\n</form>\n\n" % card_id)
        bw(u"<form method=\"POST\" action=\"/cards/%s/skip\">\n <button>Skip</button>\n</form>\n" % card_id)
    md = buf.getvalue()
    html = "<html>\n" \
        + "<head><style>%s</style></head>\n" % (css,) \
        + "<body>\n" + md2html(md) + "\n</body>\n" \
        + "</html>\n"
    response.body = html.encode('utf-8')
    response.status = '200 OK'
    response.headers = [
        ('Content-type', 'text/html')
    ]
    return response


def GET_next_card_front(request, path_match, db_conn, sql_templates, session):
    response = Obj()
    buf = StringIO()
    bw = buf.write
    if db.select_count_card(db_conn, sql_templates) == 0:
        bw(u"You have not imported any flashcard decks.\n")
    else:
        card = db.select_next_card(db_conn, sql_templates, session.session_start)
        if card is None:
            bw(u"No more cards left to review in this session.\n")
        else:
            bw(u"# Deck: %s\n" % card.deck_title)
            bw(u"- card_id: %s, score: %s\n" % (card.card_id, card.score))
            bw(u"\n\n----\n\n")
            bw(u"\n## Front of card:\n\n")
            bw(card.front)
            bw(u"\n\n----\n\n")
            bw(u"\n## Back of card:\n\n")
            back_url = "/cards/%s" % card.card_id
            bw(u"[Click to reveal](%s)\n" % back_url)
    md = buf.getvalue()
    html = "<html>\n" \
        + "<head><style>%s</style></head>\n" % (css,) \
        + "<body>\n" + md2html(md) + "\n</body>\n" \
        + "</html>\n"
    response.body = html.encode('utf-8')
    response.status = '200 OK'
    response.headers = [
        ('Content-type', 'text/html')
    ]
    return response


def GET_404(request, _, db_conn, sql_templates, session):
    """An endpoint which returns a 404 response."""
    response = Obj()
    response.body = "404".encode('utf-8')
    response.status = '404 Not Found'
    response.headers = [
        ('Content-type', 'text/plain')
    ]
    return response


g_static_routes = {
    ('GET','/'): GET_next_card_front,
    ('GET','/404'): GET_404,
}

g_dynamic_routes = [
    ('GET', r'/cards/([0-9]+)', GET_card),
    ('POST', r'/cards/([0-9]+)/did-recall', POST_did_recall),
    ('POST', r'/cards/([0-9]+)/did-not-recall', POST_did_not_recall),
    ('POST', r'/cards/([0-9]+)/skip', POST_skip),
]


def compile_routes(dynamic_routes):
    """Compiles the regexes in the routes table."""
    routes2 = []
    for (verb, path_pattern, handler_func) in dynamic_routes:
        compiled_path = re.compile("^" + path_pattern + "/*" + "$")
        entry = (verb, path_pattern, compiled_path, handler_func)
        routes2.append(entry)
        continue
    return routes2

g_compiled_dynamic_routes = compile_routes(g_dynamic_routes)


def route(request):
    """Return a handler function for the request"""
    request_verb = request['REQUEST_METHOD']
    request_path = request['PATH_INFO']

    # check for a static route
    static_key = (request_verb, request_path)
    handler_func = g_static_routes.get(static_key)
    if handler_func is not None:
        path_regex_match = None
        return (handler_func, path_regex_match)

    # check for a dynamic route
    for (route_verb, _, route_compiled_path, route_func) in g_compiled_dynamic_routes:
        if route_verb != request_verb:
            continue
        m = route_compiled_path.match(request_path)
        if m is None:
            continue
        path_regex_match = m
        handler_func = route_func
        return (handler_func, path_regex_match)

    # no match, give them 404.
    handler_func = GET_404
    path_regex_match = None
    return (handler_func, path_regex_match)


def make_application(db_conn, sql_templates, session_start):
    """Return a WSGI application function which closes over db_conn,
    sql_templates, and session_start."""
    class Context:
        # Python 2 lacks the 'nonlocal' keyword, so we use this class hack.
        # Thanks to https://stackoverflow.com/a/28433571
        session = Obj({"session_start": session_start})
    def application(request, start_response_fn):
        """A webapp request handler conforming to the WSGI interface."""
        (handler, path_regex_match) = route(request)
        response = handler(request, path_regex_match, db_conn, sql_templates, Context.session)
        body = response.get('body', b'')
        response.headers.append(
            ('Content-Length', str(len(body)))
        )
        start_response_fn(response.status, response.headers)
        return [body]
    return application
