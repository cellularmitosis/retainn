-- Update a deck.
UPDATE deck
SET
    last_fetched = :last_fetched,
    etag = :etag,
    hash = :hash,
    title = :title,
    preamble = :preamble
WHERE
    deck_id = :deck_id
