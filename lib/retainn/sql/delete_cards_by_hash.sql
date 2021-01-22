-- Delete cards from a deck by hash.
DELETE FROM card
WHERE deck_id = ? AND hash in (?...?)
