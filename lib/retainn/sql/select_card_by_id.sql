-- Select the best next card to show the user.
SELECT c.card_id, c.score, c.front, c.back, d.deck_id, d.title
FROM card c
JOIN deck d USING (deck_id)
WHERE c.card_id = :card_id
LIMIT 1;
