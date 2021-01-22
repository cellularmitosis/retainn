-- Insert a deck.
INSERT INTO deck
(gist_url, last_fetched, etag, hash, title, preamble)
VALUES
(:gist_url, :last_fetched, :etag, :hash, :title, :preamble);
