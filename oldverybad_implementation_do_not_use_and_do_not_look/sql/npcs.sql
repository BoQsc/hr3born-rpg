-- name: create_npc<!
INSERT INTO npcs (
    name, npc_type, level, room_id, attack, hit_points, max_hp,
    chaos_damage, vile_damage, elemental_attack,
    fire_resist, kinetic_resist, arcane_resist, holy_resist, shadow_resist,
    elemental_resist, gold_reward, exp_reward, loot_table,
    respawn_time, is_boss, is_raid_boss, faction_requirement, description
)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24)
RETURNING id;

-- name: get_npc_by_id
SELECT * FROM npcs WHERE id = $1;

-- name: get_npcs_in_room
SELECT * FROM npcs 
WHERE room_id = $1 AND (last_killed IS NULL OR last_killed + INTERVAL '1 second' * respawn_time <= NOW());

-- name: get_all_npcs_in_room
SELECT * FROM npcs WHERE room_id = $1;

-- name: kill_npc!
UPDATE npcs
SET last_killed = NOW()
WHERE id = $1;

-- name: get_raid_bosses
SELECT * FROM npcs
WHERE is_raid_boss = true AND (last_killed IS NULL OR last_killed + INTERVAL '1 second' * respawn_time <= NOW());

-- name: get_bosses_by_faction
SELECT * FROM npcs
WHERE is_boss = true AND faction_requirement = $1;

-- name: update_npc_stats!
UPDATE npcs
SET attack = $2, hit_points = $3, max_hp = $4,
    chaos_damage = $5, vile_damage = $6, elemental_attack = $7,
    fire_resist = $8, kinetic_resist = $9, arcane_resist = $10,
    holy_resist = $11, shadow_resist = $12, elemental_resist = $13
WHERE id = $1;