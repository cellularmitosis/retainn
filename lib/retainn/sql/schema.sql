-- sqlite3

-- The version of the database schema.
CREATE TABLE retainn_schema (
    schema_version TEXT NOT NULL
);
INSERT INTO retainn_schema (schema_version) VALUES ('1');

-- A card is all of the data associated with an individual flashcard.
CREATE TABLE card (
    card_id INTEGER PRIMARY KEY AUTOINCREMENT,
    score INTEGER NOT NULL,
    last_seen INTEGER,  -- NULL indicates "never seen"
    front TEXT NOT NULL,
    back TEXT NOT NULL,
    hash TEXT NOT NULL,
    deck_id INTEGER NOT NULL
);

-- A deck is a group of flashcards.
CREATE TABLE deck (
    deck_id INTEGER PRIMARY KEY AUTOINCREMENT,
    gist_url TEXT NOT NULL,
    last_fetched INTEGER NOT NULL,
    etag TEXT,  -- NULL indicates github stopped supporting etags.
    hash TEXT NOT NULL,
    title TEXT,  -- NULL indicates no title given in markdown.
    preamble TEXT  -- NULL indicates no preamble given in markdown.
);
