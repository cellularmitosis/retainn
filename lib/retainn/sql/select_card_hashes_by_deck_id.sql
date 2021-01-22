-- Select all of the card hashes for a particular deck.
SELECT c.hash
FROM card c
JOIN deck d USING (deck_id)
WHERE c.deck_id = :deck_id
