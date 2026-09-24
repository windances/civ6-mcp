-- Read-only. The board at T121: who we are at war with, where their cities are (visible or not),
-- which of their units are near ours, and whether a river runs between any of those pairs.
--
-- This is the reconnaissance needed to close the verification debt: supply:C/T needs an enemy city
-- that is both visible and at war, and the river -5 needs an attacker and a defender separated by a
-- river edge. Neither exists in the T121 save as it stood (the capture scan answered
-- "0 enemy cit(ies) in sight"), so the first question is whether any such pair exists at all.
local me = Game.GetLocalPlayer()
local pDiplo = Players[me]:GetDiplomacy()
local pVis = PlayersVisibility[me]

print("TURN|" .. Game.GetCurrentGameTurn())
print("US|" .. Locale.Lookup(PlayerConfigurations[me]:GetCivilizationShortDescription()))

for pid = 0, 63 do
    if pid ~= me and Players[pid] and Players[pid]:IsAlive() then
        local war, name, cities, visible = false, "?", 0, 0
        pcall(function() war = pDiplo:IsAtWarWith(pid) end)
        pcall(function()
            name = Locale.Lookup(PlayerConfigurations[pid]:GetCivilizationShortDescription())
        end)
        pcall(function()
            for _, c in Players[pid]:GetCities():Members() do
                cities = cities + 1
                if pVis:IsVisible(c:GetX(), c:GetY()) then
                    visible = visible + 1
                    local garrison = 0
                    local stack = Map.GetUnitsAt(c:GetX(), c:GetY())
                    if stack then
                        for _ in stack:Units() do garrison = garrison + 1 end
                    end
                    local hp, maxhp = 0, 0
                    local ccIdx = GameInfo.Districts["DISTRICT_CITY_CENTER"].Index
                    for _, d in c:GetDistricts():Members() do
                        if d:GetType() == ccIdx then
                            maxhp = d:GetMaxDamage(DefenseTypes.DISTRICT_GARRISON) or 0
                            hp = maxhp - (d:GetDamage(DefenseTypes.DISTRICT_GARRISON) or 0)
                            break
                        end
                    end
                    print("ENEMY_CITY|" .. pid .. "|" .. name .. "|" .. Locale.Lookup(c:GetName())
                        .. "|" .. c:GetX() .. "," .. c:GetY() .. "|hp:" .. hp .. "/" .. maxhp
                        .. "|garrison:" .. garrison .. "|war:" .. tostring(war))
                end
            end
        end)
        print("PLAYER|" .. pid .. "|" .. name .. "|war:" .. tostring(war)
            .. "|cities:" .. cities .. "|visible:" .. visible)
    end
end

-- Our military units, with the plots they could strike.
local ours = {}
for _, u in Players[me]:GetUnits():Members() do
    local info = GameInfo.Units[u:GetType()]
    local fc = info and info.FormationClass or "?"
    if fc == "FORMATION_CLASS_LAND_COMBAT" or fc == "FORMATION_CLASS_NAVAL_COMBAT" then
        local ux, uy = u:GetX(), u:GetY()
        ours[#ours + 1] = { x = ux, y = uy }
        print("OURS|" .. u:GetID() .. "|" .. (info and info.UnitType or "?") .. "|" .. ux .. "," .. uy
            .. "|hp:" .. (u:GetMaxDamage() - u:GetDamage()) .. "/" .. u:GetMaxDamage()
            .. "|moves:" .. string.format("%.1f", u:GetMovesRemaining()))
    end
end

-- Every unit of a player we are at war with, within three tiles of one of ours.
for pid = 0, 63 do
    if pid ~= me and Players[pid] and Players[pid]:IsAlive() then
        local war = false
        pcall(function() war = pDiplo:IsAtWarWith(pid) end)
        if war then
            for _, e in Players[pid]:GetUnits():Members() do
                local ex, ey = e:GetX(), e:GetY()
                local best = 99
                for _, o in ipairs(ours) do
                    local d = Map.GetPlotDistance(o.x, o.y, ex, ey)
                    if d < best then best = d end
                end
                if best <= 3 then
                    local info = GameInfo.Units[e:GetType()]
                    print("ENEMY_UNIT|" .. pid .. "|" .. e:GetID() .. "|"
                        .. (info and info.UnitType or "?") .. "|" .. ex .. "," .. ey
                        .. "|hp:" .. (e:GetMaxDamage() - e:GetDamage()) .. "/" .. e:GetMaxDamage()
                        .. "|dist:" .. best)
                end
            end
        end
    end
end

-- River flags for every plot our units stand on and their six neighbours: an attack across a
-- river is the only way to see the -5 modifier, and the flags say whether any such pair exists.
-- The method set is discovered rather than assumed: `IsNWOfRiver` does not exist on this build
-- (first run answered "function expected instead of nil"), so each is called through pcall and
-- the ones that exist are reported once.
local RIVER_DIRS = { "W", "NW", "NE", "E", "SE", "SW" }
local function flags(x, y)
    local p = Map.GetPlot(x, y)
    if not p then return "no-plot" end
    local out = {}
    for _, d in ipairs(RIVER_DIRS) do
        local fn = p["Is" .. d .. "OfRiver"]
        if type(fn) == "function" then
            local ok, v = pcall(fn, p)
            if ok and v then out[#out + 1] = d end
        end
    end
    return (#out > 0) and table.concat(out, ",") or "-"
end

if ours[1] then
    local p = Map.GetPlot(ours[1].x, ours[1].y)
    local have = {}
    for _, d in ipairs(RIVER_DIRS) do
        have[#have + 1] = d .. ":" .. tostring(type(p["Is" .. d .. "OfRiver"]) == "function")
    end
    print("RIVER_API|" .. table.concat(have, " "))
end

for _, o in ipairs(ours) do
    local river = flags(o.x, o.y)
    if river ~= "-" then
        print("RIVER|" .. o.x .. "," .. o.y .. "|on:" .. river)
    end
    for _, d in ipairs({ { 1, 0 }, { -1, 0 }, { 0, -1 }, { 0, 1 }, { 1, -1 }, { -1, 1 }, { 1, 1 }, { -1, -1 } }) do
        local nx, ny = o.x + d[1], o.y + d[2]
        local stack = Map.GetUnitsAt(nx, ny)
        if stack then
            for other in stack:Units() do
                if other:GetOwner() ~= me then
                    local oinfo = GameInfo.Units[other:GetType()]
                    print("NEIGHBOUR|" .. o.x .. "," .. o.y .. "|" .. nx .. "," .. ny
                        .. "|" .. tostring(oinfo and oinfo.UnitType or "?")
                        .. "|river_attacker:" .. flags(o.x, o.y)
                        .. "|river_defender:" .. flags(nx, ny))
                end
            end
        end
    end
end
