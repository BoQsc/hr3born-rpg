-- name: create_user<!
INSERT INTO users (username, email, password_hash, points, character_slots)
VALUES ($1, $2, $3, $4, $5)
RETURNING id, username, email, is_preferred_player, created_at, points, character_slots;

-- name: get_user_by_username
SELECT id, username, email, password_hash, is_preferred_player, created_at, last_login, points, character_slots
FROM users
WHERE username = $1;

-- name: get_user_by_email
SELECT id, username, email, password_hash, is_preferred_player, created_at, last_login, points, character_slots
FROM users
WHERE email = $1;

-- name: get_user_by_id
SELECT id, username, email, is_preferred_player, created_at, last_login, points, character_slots
FROM users
WHERE id = $1;

-- name: update_last_login!
UPDATE users
SET last_login = NOW()
WHERE id = $1;

-- name: update_user_points!
UPDATE users
SET points = points + $2
WHERE id = $1;

-- name: get_user_characters
SELECT id, name, character_class, level, experience, current_hp, hit_points, gold, faction, crew_id, last_active
FROM characters
WHERE user_id = $1
ORDER BY created_at;