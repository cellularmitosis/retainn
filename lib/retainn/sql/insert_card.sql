-- Insert a card.
INSERT INTO card
(score, last_seen, front, back, hash, deck_id)
VALUES
(:score, :last_seen, :front, :back, :hash, :deck_id);
