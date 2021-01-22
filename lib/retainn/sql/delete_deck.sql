-- Remove a deck from the database
DELETE FROM deck
WHERE gist_url = :gist_url;
