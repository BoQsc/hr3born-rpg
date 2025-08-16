-- name: create_combat_log<!
INSERT INTO combat_logs (
    attacker_id, defender_id, npc_id, combat_type, winner_id,
    log_entries, total_damage_dealt, total_damage_received,
    duration_seconds, exp_gained, gold_gained, items_gained,
    started_at, ended_at
)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
RETURNING id;

-- name: get_combat_log
SELECT * FROM combat_logs WHERE id = $1;

-- name: get_character_combat_history
SELECT 
    cl.*,
    att.name as attacker_name,
    def.name as defender_name,
    npc.name as npc_name
FROM combat_logs cl
LEFT JOIN characters att ON cl.attacker_id = att.id
LEFT JOIN characters def ON cl.defender_id = def.id
LEFT JOIN npcs npc ON cl.npc_id = npc.id
WHERE cl.attacker_id = $1 OR cl.defender_id = $1
ORDER BY cl.started_at DESC
LIMIT $2;

-- name: get_recent_pvp_battles
SELECT 
    cl.*,
    att.name as attacker_name,
    def.name as defender_name
FROM combat_logs cl
JOIN characters att ON cl.attacker_id = att.id
JOIN characters def ON cl.defender_id = def.id
WHERE cl.combat_type = 'pvp' AND cl.ended_at >= NOW() - INTERVAL '24 hours'
ORDER BY cl.started_at DESC
LIMIT $1;

-- name: update_combat_log_end!
UPDATE combat_logs
SET ended_at = $2, winner_id = $3, log_entries = $4,
    total_damage_dealt = $5, total_damage_received = $6,
    duration_seconds = $7, exp_gained = $8, gold_gained = $9,
    items_gained = $10
WHERE id = $1;