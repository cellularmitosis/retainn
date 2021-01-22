-- Delete all of the cards of a specific deck.
DELETE FROM card
WHERE deck_id = :deck_id;
