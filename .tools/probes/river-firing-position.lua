-- Read-only. Can the river -5 be made observable here?
--
-- The modifier needs our unit on one side of a river edge and an enemy on the other. At T122 no
-- such pair exists, so this looks for a *reachable* firing position instead: for every unit of a
-- player we are at war with that is within three tiles of one of ours, print its six neighbours,
-- whether a river runs between that neighbour and the enemy, and whether the tile is empty (so we
-- could stand there and attack across it).
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
        ours[#ours + 1] = { id = u:GetID(), type = info.UnitType, x = u:GetX(), y = u:GetY() }
    end
end

for pid = 0, 63 do
    if pid ~= me and Players[pid] and Players[pid]:IsAlive() and atWar(pid) then
        for _, e in Players[pid]:GetUnits():Members() do
            local ex, ey = e:GetX(), e:GetY()
            local best = 99
            for _, o in ipairs(ours) do
                local d = Map.GetPlotDistance(o.x, o.y, ex, ey)
                if d < best then best = d end
            end
            if best <= 3 then
                local einfo = GameInfo.Units[e:GetType()]
                print("ENEMY|" .. e:GetID() .. "|" .. tostring(einfo and einfo.UnitType or "?")
                    .. "|" .. ex .. "," .. ey .. "|nearest_ours:" .. best)
                local ePlot = Map.GetPlot(ex, ey)
                for dx = -1, 1 do
                    for dy = -1, 1 do
                        local nx, ny = ex + dx, ey + dy
                        if (dx ~= 0 or dy ~= 0) and Map.GetPlot(nx, ny)
                            and Map.GetPlotDistance(ex, ey, nx, ny) == 1 then
                            local ok, cross = pcall(function()
                                return ePlot:IsRiverCrossingToPlot(Map.GetPlot(nx, ny))
                            end)
                            local occupied = "-"
                            local stack = Map.GetUnitsAt(nx, ny)
                            if stack then
                                for u in stack:Units() do
                                    local i = GameInfo.Units[u:GetType()]
                                    occupied = (u:GetOwner() == me and "ours:" or "enemy:")
                                        .. tostring(i and i.UnitType or "?")
                                end
                            end
                            if (ok and cross) or occupied ~= "-" then
                                print("  SIDE|" .. nx .. "," .. ny
                                    .. "|river:" .. tostring(ok and cross or false)
                                    .. "|" .. occupied)
                            end
                        end
                    end
                end
            end
        end
    end
end
