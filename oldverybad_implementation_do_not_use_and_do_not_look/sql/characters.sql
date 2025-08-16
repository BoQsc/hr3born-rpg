-- name: create_character<!
INSERT INTO characters (user_id, name, character_class, level, experience, attack, hit_points, current_hp, max_rage, rage_per_hour, exp_per_hour, current_room_id)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
RETURNING id, name, character_class, level, experience, attack, hit_points, current_hp, gold, max_rage, created_at;

-- name: get_character_by_id
SELECT * FROM characters WHERE id = $1;

-- name: get_character_by_name
SELECT * FROM characters WHERE name = $1;

-- name: get_character_stats
SELECT 
    c.*,
    cr.name as crew_name,
    cr.leader_id as crew_leader_id,
    (SELECT COUNT(*) FROM character_relationships WHERE character_id = c.id AND relationship_type = 'ally') as ally_count
FROM characters c
LEFT JOIN crews cr ON c.crew_id = cr.id
WHERE c.id = $1;

-- name: update_character_experience!
UPDATE characters
SET experience = experience + $2, experience_yesterday = $3, level = $4
WHERE id = $1;

-- name: update_character_resources!
UPDATE characters
SET gold = $2, rage = $3, current_hp = $4, last_resource_update = NOW()
WHERE id = $1;

-- name: update_character_location!
UPDATE characters
SET current_room_id = $2, current_zone = $3, last_active = NOW()
WHERE id = $1;

-- name: update_character_stats!
UPDATE characters
SET attack = $2, hit_points = $3, chaos_damage = $4, vile_damage = $5, 
    elemental_attack = $6, elemental_resist = $7,
    fire_resist = $8, kinetic_resist = $9, arcane_resist = $10, 
    holy_resist = $11, shadow_resist = $12,
    max_rage = $13, rage_per_hour = $14, exp_per_hour = $15, gold_per_turn = $16,
    critical_hit_chance = $17, rampage_bonus = $18
WHERE id = $1;

-- name: join_crew!
UPDATE characters
SET crew_id = $2, crew_rank = $3
WHERE id = $1;

-- name: leave_crew!
UPDATE characters
SET crew_id = NULL, crew_rank = 'member'
WHERE id = $1;

-- name: set_faction!
UPDATE characters
SET faction = $2, faction_change_last_used = NOW()
WHERE id = $1;

-- name: update_faction_loyalty!
UPDATE characters
SET alvar_loyalty = $2, delruk_loyalty = $3, vordyn_loyalty = $4
WHERE id = $1;

-- name: get_characters_in_room
SELECT id, name, character_class, level, attack, hit_points, current_hp, faction, crew_id
FROM characters
WHERE current_room_id = $1 AND current_hp > 0;

-- name: get_characters_by_crew
SELECT id, name, character_class, level, attack, hit_points, current_hp, crew_rank, last_active
FROM characters
WHERE crew_id = $1
ORDER BY crew_rank DESC, level DESC;

-- name: get_top_characters_by_level
SELECT id, name, character_class, level, experience, attack, hit_points, faction, crew_id
FROM characters
ORDER BY level DESC, experience DESC
LIMIT $1;

-- name: get_character_total_power
SELECT 
    attack + hit_points + chaos_damage + vile_damage + elemental_attack + 
    fire_resist + kinetic_resist + arcane_resist + holy_resist + shadow_resist +
    max_rage/10 + critical_hit_chance*10 + rampage_bonus as total_power
FROM characters
WHERE id = $1;

-- name: heal_character!
UPDATE characters
SET current_hp = LEAST(current_hp + $2, hit_points)
WHERE id = $1;