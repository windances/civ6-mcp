-- Read-only. Find an attack that would cross a river, which is the only shape in which the
-- `river -5` modifier can be observed. The estimate applies it for melee attacks only
-- (`units.py:732-738`), so the candidate is one of our melee units adjacent to an enemy unit with
-- a river on the shared edge - asked with the same call the estimate makes,
-- `enemyPlot:IsRiverCrossingToPlot(ourPlot)`.
local me = Game.GetLocalPlayer()
local pDiplo = Players[me]:GetDiplomacy()

local function atWar(pid)
    local war = (pid == 63)
    if not war then pcall(function() war = pDiplo:IsAtWarWith(pid) end) end
    return war
end

local ours = {}
for _, u in Players[me]:GetUnits():Members() do
    local info = GameInfo.Units[u:GetType()]
    if info and ((info.Combat or 0) + (info.RangedCombat or 0)) > 0 then
        local rng = info.Range or 0
        ours[#ours + 1] = {
            id = u:GetID(), type = info.UnitType, x = u:GetX(), y = u:GetY(),
            moves = u:GetMovesRemaining(), range = rng,
            ranged = (info.RangedCombat or 0) > 0 and rng > 0,
        }
    end
end

local found = 0
for _, o in ipairs(ours) do
    local ourPlot = Map.GetPlot(o.x, o.y)
    for dx = -2, 2 do
        for dy = -2, 2 do
            local ex, ey = o.x + dx, o.y + dy
            local d = Map.GetPlotDistance(o.x, o.y, ex, ey)
            if d >= 1 and d <= 2 and Map.GetPlot(ex, ey) then
                local stack = Map.GetUnitsAt(ex, ey)
                if stack then
                    for e in stack:Units() do
                        local owner = e:GetOwner()
                        if owner ~= me and atWar(owner) then
                            local einfo = GameInfo.Units[e:GetType()]
                            local ehp = e:GetMaxDamage() - e:GetDamage()
                            local cross, err = pcall(function()
                                return Map.GetPlot(ex, ey):IsRiverCrossingToPlot(ourPlot)
                            end)
                            -- pcall's *first* return is its status, not the answer: reading it
                            -- directly made every pair look like a river crossing (including one
                            -- sixteen tiles away), which is how a false "the river -5 is missing"
                            -- reached the estimate. Take the second value, and `false` on error.
                            local crossing = (cross == true) and (err == true) or false
                            local legal = o.ranged and d <= o.range or (not o.ranged and d == 1)
                            found = found + 1
                            print("PAIR|" .. o.type .. "|" .. o.id .. "|" .. o.x .. "," .. o.y
                                .. "|" .. (einfo and einfo.UnitType or "?") .. "|" .. e:GetID()
                                .. "|" .. ex .. "," .. ey .. "|dist:" .. d
                                .. "|ehp:" .. ehp .. "|our_moves:" .. string.format("%.1f", o.moves)
                                .. "|river:" .. tostring(crossing)
                                .. "|legal:" .. tostring(legal))
                        end
                    end
                end
            end
        end
    end
end
print("PAIRS|" .. found)
