-- name: get_account_by_username^
SELECT * FROM accounts WHERE username = :username;

-- name: create_account!
INSERT INTO accounts (username, password_hash, email) VALUES (:username, :password_hash, :email);

-- name: get_character_by_id^
SELECT c.*, cc.name as class_name, cc.attack_bonus, cc.defense_bonus, cc.rage_per_turn_bonus, cc.max_rage_bonus,
       f.name as faction_name
FROM characters c
JOIN character_classes cc ON c.class_id = cc.id
LEFT JOIN factions f ON c.faction_id = f.id
WHERE c.id = :character_id;

-- name: get_characters_by_account
SELECT c.*, cc.name as class_name FROM characters c
JOIN character_classes cc ON c.class_id = cc.id
WHERE c.account_id = :account_id
ORDER BY c.last_active DESC;

-- name: create_character!
INSERT INTO characters (account_id, name, class_id, current_room_id) VALUES (:account_id, :name, :class_id, 1);

-- name: update_character_stats!
UPDATE characters SET 
    level = :level, experience = :experience, gold = :gold, rage_current = :rage_current, rage_max = :rage_max,
    hit_points_current = :hit_points_current, hit_points_max = :hit_points_max, attack = :attack, total_power = :total_power,
    last_active = CURRENT_TIMESTAMP
WHERE id = :character_id;

-- name: get_character_equipment
SELECT ce.slot_id, ce.item_id, i.name, i.attack, i.hit_points, i.chaos_damage, i.vile_damage,
       i.fire_damage, i.kinetic_damage, i.arcane_damage, i.holy_damage, i.shadow_damage,
       i.fire_resist, i.kinetic_resist, i.arcane_resist, i.holy_resist, i.shadow_resist,
       i.critical_hit_percent, i.rampage_percent, i.rage_per_hour, i.experience_per_hour,
       i.gold_per_turn, i.max_rage, es.name as slot_name, ir.name as rarity_name, ir.color
FROM character_equipment ce
JOIN items i ON ce.item_id = i.id
JOIN equipment_slots es ON ce.slot_id = es.id
JOIN item_rarities ir ON i.rarity_id = ir.id
WHERE ce.character_id = :character_id;

-- name: equip_item!
INSERT OR REPLACE INTO character_equipment (character_id, slot_id, item_id) VALUES (:character_id, :slot_id, :item_id);

-- name: unequip_item!
DELETE FROM character_equipment WHERE character_id = :character_id AND slot_id = :slot_id;

-- name: get_character_inventory
SELECT ci.id, ci.item_id, ci.quantity, ci.transfers_remaining,
       i.name, i.level_requirement, i.attack, i.hit_points,
       es.name as slot_name, ir.name as rarity_name, ir.color
FROM character_inventory ci
JOIN items i ON ci.item_id = i.id
JOIN equipment_slots es ON i.slot_id = es.id
JOIN item_rarities ir ON i.rarity_id = ir.id
WHERE ci.character_id = :character_id
ORDER BY i.slot_id, i.name;

-- name: add_to_inventory!
INSERT INTO character_inventory (character_id, item_id, quantity, transfers_remaining)
VALUES (:character_id, :item_id, :quantity, :transfers_remaining);

-- name: remove_from_inventory!
DELETE FROM character_inventory WHERE character_id = :character_id AND item_id = :item_id;

-- name: get_room_info^
SELECT r.*, z.name as zone_name, z.description as zone_description
FROM rooms r
JOIN zones z ON r.zone_id = z.id
WHERE r.id = :room_id;

-- name: get_room_connections
SELECT rc.direction, rc.to_room_id, r.name as room_name
FROM room_connections rc
JOIN rooms r ON rc.to_room_id = r.id
WHERE rc.from_room_id = :room_id;

-- name: move_character!
UPDATE characters SET current_room_id = :room_id WHERE id = :character_id;

-- name: get_characters_in_room
SELECT c.id, c.name, c.level, cc.name as class_name, c.total_power
FROM characters c
JOIN character_classes cc ON c.class_id = cc.id
WHERE c.current_room_id = :room_id AND c.hit_points_current > 0
ORDER BY c.total_power DESC;

-- name: create_crew!
INSERT INTO crews (name, leader_id, description) VALUES (:name, :leader_id, :description);

-- name: get_crew_by_character^
SELECT cr.*, c.name as leader_name
FROM crews cr
JOIN crew_members cm ON cr.id = cm.crew_id
JOIN characters c ON cr.leader_id = c.id
WHERE cm.character_id = :character_id;

-- name: join_crew!
INSERT INTO crew_members (crew_id, character_id, role) VALUES (:crew_id, :character_id, :role);

-- name: get_crew_members
SELECT c.id, c.name, c.level, cc.name as class_name, cm.role, cm.joined_at
FROM crew_members cm
JOIN characters c ON cm.character_id = c.id
JOIN character_classes cc ON c.class_id = cc.id
WHERE cm.crew_id = :crew_id
ORDER BY cm.role DESC, c.level DESC;

-- name: get_crew_vault
SELECT cv.id, cv.item_id, cv.quantity, i.name, ir.name as rarity_name, ir.color,
       c.name as deposited_by_name, cv.deposited_at
FROM crew_vault cv
JOIN items i ON cv.item_id = i.id
JOIN item_rarities ir ON i.rarity_id = ir.id
LEFT JOIN characters c ON cv.deposited_by = c.id
WHERE cv.crew_id = :crew_id
ORDER BY cv.deposited_at DESC;

-- name: add_to_crew_vault!
INSERT INTO crew_vault (crew_id, item_id, quantity, deposited_by) VALUES (:crew_id, :item_id, :quantity, :deposited_by);

-- name: remove_from_crew_vault!
DELETE FROM crew_vault WHERE id = :vault_item_id;

-- name: award_from_crew_vault!
UPDATE crew_vault SET crew_id = NULL WHERE id = :vault_item_id;

-- name: log_combat!
INSERT INTO combat_logs (attacker_id, defender_id, attacker_damage, defender_damage,
                        attacker_hp_before, attacker_hp_after, defender_hp_before, defender_hp_after,
                        winner_id, experience_gained, gold_gained, combat_type)
VALUES (:attacker_id, :defender_id, :attacker_damage, :defender_damage,
        :attacker_hp_before, :attacker_hp_after, :defender_hp_before, :defender_hp_after,
        :winner_id, :experience_gained, :gold_gained, :combat_type);

-- name: get_combat_history
SELECT cl.*, 
       ca.name as attacker_name, cd.name as defender_name, cw.name as winner_name
FROM combat_logs cl
JOIN characters ca ON cl.attacker_id = ca.id
LEFT JOIN characters cd ON cl.defender_id = cd.id
LEFT JOIN characters cw ON cl.winner_id = cw.id
WHERE cl.attacker_id = :character_id OR cl.defender_id = :character_id
ORDER BY cl.created_at DESC
LIMIT 20;

-- name: create_session!
INSERT INTO sessions (id, account_id, expires_at) VALUES (:session_id, :account_id, :expires_at);

-- name: get_session
SELECT s.*, a.username FROM sessions s
JOIN accounts a ON s.account_id = a.id
WHERE s.id = :session_id AND s.expires_at > CURRENT_TIMESTAMP;

-- name: delete_session!
DELETE FROM sessions WHERE id = :session_id;

-- name: cleanup_expired_sessions!
DELETE FROM sessions WHERE expires_at <= CURRENT_TIMESTAMP;

-- name: get_all_classes
SELECT * FROM character_classes ORDER BY id;

-- name: get_all_factions
SELECT * FROM factions ORDER BY id;

-- name: get_items_by_slot
SELECT i.*, ir.name as rarity_name, ir.color, es.name as slot_name
FROM items i
JOIN item_rarities ir ON i.rarity_id = ir.id
JOIN equipment_slots es ON i.slot_id = es.id
WHERE i.slot_id = :slot_id AND i.level_requirement <= :character_level
ORDER BY i.rarity_id DESC, i.attack + i.hit_points DESC;

-- name: calculate_character_total_power^
SELECT 
    c.attack + c.hit_points_max + 
    (c.fire_damage + c.kinetic_damage + c.arcane_damage + c.holy_damage + c.shadow_damage) +
    c.chaos_damage + c.vile_damage +
    (c.fire_resist + c.kinetic_resist + c.arcane_resist + c.holy_resist + c.shadow_resist) / 10 +
    COALESCE(SUM(
        i.attack + i.hit_points + 
        (i.fire_damage + i.kinetic_damage + i.arcane_damage + i.holy_damage + i.shadow_damage) +
        i.chaos_damage + i.vile_damage +
        (i.fire_resist + i.kinetic_resist + i.arcane_resist + i.holy_resist + i.shadow_resist) / 10
    ), 0) as total_power
FROM characters c
LEFT JOIN character_equipment ce ON c.id = ce.character_id
LEFT JOIN items i ON ce.item_id = i.id
WHERE c.id = :character_id
GROUP BY c.id;

-- name: update_character_total_power!
UPDATE characters SET total_power = :total_power WHERE id = :character_id;