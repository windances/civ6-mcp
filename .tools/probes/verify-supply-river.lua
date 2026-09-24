-- Read-only. Two things, for the enemy city the capture scan just reported at T113 (St Petersburg,
-- (56,43), supply:2/6):
--
-- 1. Re-derive the supply count independently of the adapter: list the six hexes adjacent to the
--    city and, for each, whether one of our combat units stands on it (directly cut) or stands
--    beside it (cut by zone of control). The manual's rule is "a supply line is any hex adjacent
--    to the city that is not within an enemy unit's Zone of Control", so this count is the whole
--    mechanic. Compare the total with the `supply:2/6` the query printed.
-- 2. For every one of our units within two tiles, ask the same call the estimate uses
--    (`units.py:734` -> `tgtPlot:IsRiverCrossingToPlot(attPlot)`) whether an attack on the city
--    would cross a river. Whichever unit answers true is the one whose estimate must print
--    `river -5`.
local CITY_X, CITY_Y = 56, 43
local me = Game.GetLocalPlayer()
local cityPlot = Map.GetPlot(CITY_X, CITY_Y)

local function isFighter(info)
    return info and ((info.Combat or 0) + (info.RangedCombat or 0)) > 0
end

local function oursOn(x, y)
    local stack = Map.GetUnitsAt(x, y)
    if not stack then return nil end
    for u in stack:Units() do
        if u:GetOwner() == me then
            local info = GameInfo.Units[u:GetType()]
            if isFighter(info) then return info.UnitType end
        end
    end
    return nil
end

print("CITY|" .. Locale.Lookup(Cities.GetCityInPlot(CITY_X, CITY_Y):GetName())
    .. "|" .. CITY_X .. "," .. CITY_Y)

local total, cut = 0, 0
for dx = -1, 1 do
    for dy = -1, 1 do
        local nx, ny = CITY_X + dx, CITY_Y + dy
        if (dx ~= 0 or dy ~= 0) and Map.GetPlot(nx, ny)
            and Map.GetPlotDistance(CITY_X, CITY_Y, nx, ny) == 1 then
            total = total + 1
            local direct = oursOn(nx, ny)
            local zocUnit, zocAt = nil, nil
            if not direct then
                for zx = -1, 1 do
                    for zy = -1, 1 do
                        local ax, ay = nx + zx, ny + zy
                        if (zx ~= 0 or zy ~= 0) and Map.GetPlotDistance(nx, ny, ax, ay) == 1 then
                            local near = oursOn(ax, ay)
                            if near and not zocUnit then
                                zocUnit, zocAt = near, ax .. "," .. ay
                            end
                        end
                    end
                end
            end
            local state = direct and ("cut-by-unit:" .. direct)
                or (zocUnit and ("cut-by-zoc:" .. zocUnit .. "@" .. zocAt) or "OPEN")
            if direct or zocUnit then cut = cut + 1 end
            print("HEX|" .. nx .. "," .. ny .. "|" .. state)
        end
    end
end
print("SUPPLY|" .. cut .. "/" .. total)

local riverPairs = 0
for dx = -1, 1 do
    for dy = -1, 1 do
        local ux, uy = CITY_X + dx, CITY_Y + dy
        local stack = Map.GetUnitsAt(ux, uy)
        if stack then
            for u in stack:Units() do
                if u:GetOwner() == me then
                    local info = GameInfo.Units[u:GetType()]
                    if isFighter(info) then
                        local attPlot = Map.GetPlot(ux, uy)
                        local crossing, err = pcall(function()
                            return cityPlot:IsRiverCrossingToPlot(attPlot)
                        end)
                        local d = Map.GetPlotDistance(ux, uy, CITY_X, CITY_Y)
                        if crossing == true then riverPairs = riverPairs + 1 end
                        print("ATTACKER|" .. u:GetID() .. "|" .. info.UnitType .. "|" .. ux .. "," .. uy
                            .. "|dist:" .. d
                            .. "|hp:" .. (u:GetMaxDamage() - u:GetDamage()) .. "/" .. u:GetMaxDamage()
                            .. "|moves:" .. string.format("%.1f", u:GetMovesRemaining())
                            .. "|river_crossing:" .. tostring(crossing)
                            .. (type(err) == "string" and ("|err:" .. err:sub(1, 40)) or ""))
                    end
                end
            end
        end
    end
end
print("RIVER_ATTACKERS|" .. riverPairs)
