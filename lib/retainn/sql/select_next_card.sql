-- Select the best next card to show the user.
SELECT c.card_id, c.score, c.front, c.back, d.deck_id, d.title
FROM card c
JOIN deck d USING (deck_id)
WHERE last_seen < :session_start OR last_seen IS NULL
ORDER BY score ASC, last_seen ASC, card_id ASC
LIMIT 1;
