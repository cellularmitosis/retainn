-- Update the card's score and last_seen values.
UPDATE card
SET score = :score, last_seen = :last_seen
WHERE card_id = :card_id
