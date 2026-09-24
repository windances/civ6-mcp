-- GameCore. Grant the civic chain that unlocks Corps, for a *verification* run only.
--
-- The human approved this explicitly: the branch is a throwaway reload of AutoSave_0120 and the
-- point is to test `UnitCommandTypes.FORM_CORPS` end to end. Nationalism is Industrial-era and
-- unreachable by play here, so this is a cheat, and it is written down as one.
--
-- The player's civic object is `Players[me]:GetCulture()` (there is no GetCivics - that was the
-- first thing this probe got wrong: "function expected instead of nil"), per `lua/tech.py:309`.
-- The setter is discovered rather than assumed; the prerequisite chain is walked in order
-- (Medieval Faires -> Humanism -> The Enlightenment -> Nationalism) and adopted state is reported
-- after each step, so a refusal says which link failed.
local me = Game.GetLocalPlayer()
local p = Players[me]
local c = p:GetCulture()
print("CULTURE|type:" .. tostring(type(c)))

for _, name in ipairs({ "HasCivic", "GetCivicProgress", "SetProgress", "SetCivicProgress",
    "AddProgress", "SetProgressAmount", "SetProgressingCivic", "SetCivicAdopted", "SetAdopted" }) do
    print("METHOD|" .. name .. "|" .. tostring(type(c[name])))
end

local chain = { "CIVIC_MEDIEVAL_FAIRES", "CIVIC_HUMANISM", "CIVIC_THE_ENLIGHTENMENT",
    "CIVIC_NATIONALISM" }
local idx = {}
for _, key in ipairs(chain) do
    local row = GameInfo.Civics[key]
    if row then
        idx[key] = row.Index
        local ok, has = pcall(function() return c:HasCivic(row.Index) end)
        print("BEFORE|" .. key .. "|index:" .. row.Index .. "|adopted:" .. tostring(ok and has))
    else
        print("BEFORE|" .. key .. "|no such civic row")
    end
end

for _, key in ipairs(chain) do
    if idx[key] then
        local applied = {}
        for _, name in ipairs({ "SetProgress", "SetCivicProgress", "AddProgress" }) do
            if type(c[name]) == "function" then
                local ok = pcall(function() c[name](c, idx[key], 99999) end)
                applied[#applied + 1] = name .. ":" .. tostring(ok)
            end
        end
        local ok, has = pcall(function() return c:HasCivic(idx[key]) end)
        print("GRANT|" .. key .. "|" .. (#applied > 0 and table.concat(applied, ",") or "no-setter")
            .. "|adopted:" .. tostring(ok and has))
    end
end
