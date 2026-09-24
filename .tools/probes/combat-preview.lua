-- Read-only. Ask the game itself what an attack would do.
--
-- `CombatManager.SimulateAttackVersus(attackerComponentID, defenderComponentID, eCombatType)` is
-- what the game's own unit panel uses to draw the combat preview
-- (`Base/Assets/UI/Panels/UnitPanel.lua:3352`, and `SimulateAttackInto` for a location). It is
-- available in the InGame state, so our estimate can be checked against the engine rather than
-- against the manual alone. The result table is indexed by `CombatResultParameters.*`, so those
-- names are printed first.
--
-- The pair below is the T113 one the estimate was run on: our Heavy Chariot (id 1310724) in
-- Moscow against the Russian Warrior at (53,40). Our estimate said: attCS 34 (28 + flank 6),
-- defCS 20, ~70 damage to the defender, ~8 to the attacker.
local CRP_NAME = {}
for k, v in pairs(CombatResultParameters) do
    CRP_NAME[v] = k
end

local ATTACKER_ID, DEFENDER_ID = 1310724, 589827
local me = Game.GetLocalPlayer()
local attacker, defender
for _, u in Players[me]:GetUnits():Members() do
    if u:GetID() == ATTACKER_ID then attacker = u end
end
for pid = 0, 63 do
    if Players[pid] and Players[pid]:IsAlive() then
        pcall(function()
            for _, u in Players[pid]:GetUnits():Members() do
                if u:GetID() == DEFENDER_ID then defender = u end
            end
        end)
    end
end

if not attacker or not defender then
    print("MISSING|attacker:" .. tostring(attacker ~= nil) .. "|defender:" .. tostring(defender ~= nil))
    return
end

local ainfo = GameInfo.Units[attacker:GetType()]
local dinfo = GameInfo.Units[defender:GetType()]
print("PAIR|" .. ainfo.UnitType .. "|" .. attacker:GetX() .. "," .. attacker:GetY()
    .. "|" .. dinfo.UnitType .. "|" .. defender:GetX() .. "," .. defender:GetY()
    .. "|dist:" .. Map.GetPlotDistance(attacker:GetX(), attacker:GetY(), defender:GetX(), defender:GetY()))

local ok, res = pcall(function()
    return CombatManager.SimulateAttackVersus(
        attacker:GetComponentID(), defender:GetComponentID(), nil)
end)
if not ok then
    print("SIM|failed:" .. tostring(res))
    return
end

local function dump(t, prefix, depth)
    if type(t) ~= "table" or depth > 3 then return end
    for k, v in pairs(t) do
        -- The nested tables are keyed by the CombatResultParameters *values*, so the reverse map
        -- is what makes the dump readable ("DEFENDER.DAMAGE_TO" rather than "-1632097141.1930175143").
        local key = CRP_NAME[k] or tostring(k)
        if type(v) == "table" then
            dump(v, prefix .. key .. ".", depth + 1)
        else
            print("RES|" .. prefix .. key .. "=" .. tostring(v))
        end
    end
end
dump(res, "", 0)
