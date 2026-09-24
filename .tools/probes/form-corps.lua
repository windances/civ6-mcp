-- InGame. Form a Corps and report what changed - the end-to-end check for FORM_CORPS.
--
-- The call shape comes from the game's own code, not from guessing
-- (`Base/Assets/UI/WorldInput.lua:2877-2882`, the Form Corps interface mode):
--
--     local tParameters = {}
--     tParameters[UnitCommandTypes.PARAM_UNIT_PLAYER] = partner:GetOwner()
--     tParameters[UnitCommandTypes.PARAM_UNIT_ID] = partner:GetID()
--     if UnitManager.CanStartCommand(selected, UnitCommandTypes.FORM_CORPS, tParameters) then
--         UnitManager.RequestCommand(selected, UnitCommandTypes.FORM_CORPS, tParameters)
--     end
--
-- and the partner candidates come from `UnitManager.GetCommandTargets(selected, FORM_CORPS)`
-- (`WorldInput.lua:2900`), which is what the UI highlights as valid partners.
--
-- Read-only unless FORM is true: then it forms one Corps from the first target pair.
local me = Game.GetLocalPlayer()
local FORM = FORM_OR_NOT  -- replaced by the Python caller: true to actually form

local function describe(u)
    local info = GameInfo.Units[u:GetType()]
    local formation = "?"
    pcall(function() formation = tostring(u:GetMilitaryFormation()) end)
    return (info and info.UnitType or "?") .. "#" .. u:GetID()
        .. "@" .. u:GetX() .. "," .. u:GetY()
        .. " hp" .. (u:GetMaxDamage() - u:GetDamage()) .. "/" .. u:GetMaxDamage()
        .. " cs" .. tostring(info and info.Combat or "?")
        .. " formation:" .. formation
end

local ours = {}
for _, u in Players[me]:GetUnits():Members() do
    local info = GameInfo.Units[u:GetType()]
    if info and info.FormationClass == "FORMATION_CLASS_LAND_COMBAT" then
        ours[#ours + 1] = u
    end
end
print("UNITS|" .. #ours)

local pair = nil
for _, u in ipairs(ours) do
    local ok, res = pcall(function()
        return UnitManager.GetCommandTargets(u, UnitCommandTypes.FORM_CORPS)
    end)
    local targets = ok and res and res[UnitCommandResults.UNITS] or nil
    if targets and #targets > 0 then
        for _, t in ipairs(targets) do
            print("TARGET|" .. describe(u) .. " <- " .. describe(t))
            if not pair then pair = { u, t } end
        end
    end
end

if not pair then
    print("PAIR|none: no unit has a FORM_CORPS target")
    return
end
print("PAIR|" .. describe(pair[1]) .. " <- " .. describe(pair[2]))

local params = {}
params[UnitCommandTypes.PARAM_UNIT_PLAYER] = pair[2]:GetOwner()
params[UnitCommandTypes.PARAM_UNIT_ID] = pair[2]:GetID()
local can = "?"
pcall(function()
    can = tostring(UnitManager.CanStartCommand(pair[1], UnitCommandTypes.FORM_CORPS, params))
end)
print("CAN|" .. can)
if not FORM then
    print("FORM|skipped (read-only run)")
    return
end
if can ~= "true" then
    print("FORM|refused: CanStartCommand said " .. can)
    return
end

local beforeCount = #ours
pcall(function()
    UnitManager.RequestCommand(pair[1], UnitCommandTypes.FORM_CORPS, params)
end)

print("FORM|issued")
-- Re-read after the request: the merged unit should carry the formation and one unit is gone.
for _, u in Players[me]:GetUnits():Members() do
    local info = GameInfo.Units[u:GetType()]
    if info and info.UnitType == "UNIT_HEAVY_CHARIOT" then
        print("AFTER|" .. describe(u))
    end
end
local after = 0
for _, u in Players[me]:GetUnits():Members() do
    local info = GameInfo.Units[u:GetType()]
    if info and info.FormationClass == "FORMATION_CLASS_LAND_COMBAT" then
        after = after + 1
    end
end
print("COUNT|" .. beforeCount .. " -> " .. after)
