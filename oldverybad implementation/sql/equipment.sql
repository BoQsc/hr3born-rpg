-- name: create_item_template<!
INSERT INTO item_templates (
    name, item_type, slot, rarity, level_requirement,
    attack_bonus, hp_bonus, chaos_damage_bonus, vile_damage_bonus, elemental_attack_bonus,
    fire_resist_bonus, kinetic_resist_bonus, arcane_resist_bonus, holy_resist_bonus, shadow_resist_bonus,
    elemental_resist_bonus, rage_per_hour_bonus, exp_per_hour_bonus, gold_per_turn_bonus,
    max_rage_bonus, critical_hit_bonus, rampage_bonus,
    can_transfer, max_transfers_per_day, is_raidbound, description
)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26)
RETURNING id;

-- name: get_item_template_by_id
SELECT * FROM item_templates WHERE id = $1;

-- name: get_item_templates_by_type
SELECT * FROM item_templates WHERE item_type = $1 ORDER BY level_requirement, rarity;

-- name: get_character_items
SELECT 
    ci.id, ci.equipped_slot, ci.is_equipped, ci.inventory_position,
    ci.transfers_today, ci.augments, ci.custom_stats,
    it.name, it.item_type, it.slot, it.rarity, it.level_requirement,
    it.attack_bonus, it.hp_bonus, it.chaos_damage_bonus, it.vile_damage_bonus,
    it.elemental_attack_bonus, it.fire_resist_bonus, it.kinetic_resist_bonus,
    it.arcane_resist_bonus, it.holy_resist_bonus, it.shadow_resist_bonus,
    it.elemental_resist_bonus, it.rage_per_hour_bonus, it.exp_per_hour_bonus,
    it.gold_per_turn_bonus, it.max_rage_bonus, it.critical_hit_bonus,
    it.rampage_bonus, it.can_transfer, it.max_transfers_per_day, it.description
FROM character_items ci
JOIN item_templates it ON ci.item_template_id = it.id
WHERE ci.character_id = $1
ORDER BY ci.is_equipped DESC, ci.inventory_position;

-- name: get_character_equipped_items
SELECT 
    ci.id, ci.equipped_slot,
    it.name, it.item_type, it.slot, it.rarity,
    it.attack_bonus, it.hp_bonus, it.chaos_damage_bonus, it.vile_damage_bonus,
    it.elemental_attack_bonus, it.fire_resist_bonus, it.kinetic_resist_bonus,
    it.arcane_resist_bonus, it.holy_resist_bonus, it.shadow_resist_bonus,
    it.elemental_resist_bonus, it.rage_per_hour_bonus, it.exp_per_hour_bonus,
    it.gold_per_turn_bonus, it.max_rage_bonus, it.critical_hit_bonus, it.rampage_bonus
FROM character_items ci
JOIN item_templates it ON ci.item_template_id = it.id
WHERE ci.character_id = $1 AND ci.is_equipped = true;

-- name: give_item_to_character<!
INSERT INTO character_items (character_id, item_template_id, inventory_position)
VALUES ($1, $2, $3)
RETURNING id;

-- name: equip_item!
UPDATE character_items
SET is_equipped = true, equipped_slot = $2, inventory_position = NULL
WHERE id = $1 AND character_id = $3;

-- name: unequip_item!
UPDATE character_items
SET is_equipped = false, equipped_slot = NULL, inventory_position = $2
WHERE id = $1 AND character_id = $3;

-- name: transfer_item!
UPDATE character_items
SET character_id = $2, transfers_today = transfers_today + 1,
    transfer_history = transfer_history || $3::jsonb
WHERE id = $1;

-- name: get_crew_vault_items
SELECT 
    cvi.id, cvi.vault_position, cvi.deposited_at,
    c.name as deposited_by_name,
    it.name, it.item_type, it.slot, it.rarity, it.level_requirement,
    it.attack_bonus, it.hp_bonus, it.chaos_damage_bonus, it.vile_damage_bonus,
    it.elemental_attack_bonus, it.fire_resist_bonus, it.kinetic_resist_bonus,
    it.arcane_resist_bonus, it.holy_resist_bonus, it.shadow_resist_bonus,
    it.elemental_resist_bonus, it.rage_per_hour_bonus, it.exp_per_hour_bonus,
    it.gold_per_turn_bonus, it.max_rage_bonus, it.critical_hit_bonus,
    it.rampage_bonus, it.description
FROM crew_vault_items cvi
JOIN item_templates it ON cvi.item_template_id = it.id
LEFT JOIN characters c ON cvi.deposited_by = c.id
WHERE cvi.crew_id = $1
ORDER BY cvi.vault_position;

-- name: deposit_item_to_vault<!
INSERT INTO crew_vault_items (crew_id, item_template_id, deposited_by, vault_position, augments, custom_stats)
SELECT $1, ci.item_template_id, $2, $3, ci.augments, ci.custom_stats
FROM character_items ci
WHERE ci.id = $4;

-- name: remove_item_from_character!
DELETE FROM character_items WHERE id = $1 AND character_id = $2;

-- name: award_vault_item_to_character<!
INSERT INTO character_items (character_id, item_template_id, inventory_position, augments, custom_stats)
SELECT $1, cvi.item_template_id, $2, cvi.augments, cvi.custom_stats
FROM crew_vault_items cvi
WHERE cvi.id = $3
RETURNING id;

-- name: remove_vault_item!
DELETE FROM crew_vault_items WHERE id = $1 AND crew_id = $2;

-- name: get_next_inventory_position
SELECT COALESCE(MAX(inventory_position), 0) + 1
FROM character_items
WHERE character_id = $1 AND is_equipped = false;

-- name: get_next_vault_position
SELECT COALESCE(MAX(vault_position), 0) + 1
FROM crew_vault_items
WHERE crew_id = $1;