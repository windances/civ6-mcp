-- Read-only. Can a Corps/Army be formed from Lua here, and what does the game expose for it?
--
-- `prompts/tactics/01-unit-production.md` tells the agent that Corps (+10 CS, Nationalism) and
-- Armies (+7 more, Mobilization) are the late-game scaling lever and that the adapter cannot form
-- them yet. The evidence that they exist at all is UI-side (UnitPanel.lua:488/494,
-- MapTacks.lua:318 -> UnitCommandTypes.FORM_CORPS / FORM_ARMY). This probe asks the InGame state
-- what is visible from here: the enum, the civics, our same-type unit pairs, and whether the
-- command can be started. Nothing is ordered.
for k, v in pairs(UnitCommandTypes or {}) do
    if string.find(k, "CORPS") or string.find(k, "ARMY") or string.find(k, "ESCORT")
        or string.find(k, "FORMATION") then
        print("CMD|" .. k .. "=" .. tostring(v))
    end
end

print("UNITMANAGER|" .. tostring(type(UnitManager)))
print("UNITCOMMANDTYPES|" .. tostring(type(UnitCommandTypes)))

local me = Game.GetLocalPlayer()
local p = Players[me]

for _, civic in ipairs({ "CIVIC_NATIONALISM", "CIVIC_MOBILIZATION", "CIVIC_MERCENARIES" }) do
    local row = GameInfo.Civics[civic]
    print("ROW|" .. civic .. "|index:" .. tostring(row and row.Index or "nil"))
    if row then
        -- `HasCivic` answers for the local player; the pcall result is printed either way,
        -- because "the call failed" and "not researched" are different answers.
        local ok, res = pcall(function() return p:GetCivics():HasCivic(row.Index) end)
        print("HAS|" .. civic .. "|ok:" .. tostring(ok) .. "|researched:" .. tostring(res))
    end
end

local counts, sample = {}, {}
for _, u in p:GetUnits():Members() do
    local info = GameInfo.Units[u:GetType()]
    if info and info.FormationClass == "FORMATION_CLASS_LAND_COMBAT" then
        counts[info.UnitType] = (counts[info.UnitType] or 0) + 1
        if not sample[info.UnitType] then sample[info.UnitType] = u end
        local xp = "n/a"
        pcall(function() xp = u:GetExperience() end)
        print("UNIT|" .. u:GetID() .. "|" .. info.UnitType
            .. "|" .. u:GetX() .. "," .. u:GetY()
            .. "|xp:" .. tostring(xp))
    end
end
for k, v in pairs(counts) do
    print("COUNT|" .. k .. "=" .. v)
end

-- The two commands the UI offers, asked of one unit of each type. InGame may not carry
-- UnitManager (it is a UI global), which is itself the answer we need before building a tool.
for k, u in pairs(sample) do
    for _, cmd in ipairs({ "FORM_CORPS", "FORM_ARMY", "UPGRADE" }) do
        local ctype = UnitCommandTypes and UnitCommandTypes[cmd]
        if ctype then
            local can = "no-UnitManager"
            pcall(function()
                can = tostring(UnitManager.CanStartCommand(u, ctype, false))
            end)
            print("CAN|" .. k .. "|" .. cmd .. "=" .. tostring(ctype) .. "|" .. can)
        end
    end
end
