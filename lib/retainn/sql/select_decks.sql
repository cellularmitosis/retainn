-- Select all of the flashcard decks.
SELECT
    d.deck_id, d.gist_url, d.last_fetched, d.etag, d.hash, d.title, d.preamble
FROM deck d;
