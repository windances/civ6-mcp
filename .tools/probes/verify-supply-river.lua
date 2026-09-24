-- Read-only. Re-derive `supply:C/T` for every visible enemy city, independently of the adapter.
--
-- The manual's rule (HEALING DAMAGE TO CITIES): "A supply line is any hex adjacent to the city
-- that is not within an enemy unit's Zone of Control" - so the count is the whole mechanic, and
-- this walks the six hexes itself rather than trusting the query:
--   cut-by-unit:<our unit on the hex>       directly occupied
--   cut-by-zoc:<our unit beside the hex>    inside our zone of control
--   OPEN                                    a supply line
-- Compare the total with the `supply:C/T` field on the adapter's own CAPTURE_READY line.
--
-- It also asks, for every one of our units within two tiles, whether an attack on the city tile
-- would cross a river (`units.py:734` uses the same call), which is the only way to see the
-- `river -5` modifier.
local me = Game.GetLocalPlayer()
local pDiplo = Players[me]:GetDiplomacy()
local pVis = PlayersVisibility[me]

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

local function atWar(pid)
    local war = (pid == 63)
    if not war then pcall(function() war = pDiplo:IsAtWarWith(pid) end) end
    return war
end

for pid = 0, 63 do
    if pid ~= me and Players[pid] and Players[pid]:IsAlive() and atWar(pid) then
        pcall(function()
            for _, c in Players[pid]:GetCities():Members() do
                local cx, cy = c:GetX(), c:GetY()
                if pVis:IsVisible(cx, cy) then
                    print("CITY|" .. Locale.Lookup(c:GetName()) .. "|" .. cx .. "," .. cy
                        .. "|owner:" .. pid)
                    local total, cut = 0, 0
                    for dx = -1, 1 do
                        for dy = -1, 1 do
                            local nx, ny = cx + dx, cy + dy
                            if (dx ~= 0 or dy ~= 0) and Map.GetPlot(nx, ny)
                                and Map.GetPlotDistance(cx, cy, nx, ny) == 1 then
                                total = total + 1
                                local direct = oursOn(nx, ny)
                                local zocUnit, zocAt = nil, nil
                                if not direct then
                                    for zx = -1, 1 do
                                        for zy = -1, 1 do
                                            local ax, ay = nx + zx, ny + zy
                                            if (zx ~= 0 or zy ~= 0)
                                                and Map.GetPlotDistance(nx, ny, ax, ay) == 1 then
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
                                print("  HEX|" .. nx .. "," .. ny .. "|" .. state)
                            end
                        end
                    end
                    print("  SUPPLY|" .. cut .. "/" .. total)

                    local cityPlot = Map.GetPlot(cx, cy)
                    for dx = -1, 1 do
                        for dy = -1, 1 do
                            local ux, uy = cx + dx, cy + dy
                            local stack = Map.GetUnitsAt(ux, uy)
                            if stack then
                                for u in stack:Units() do
                                    if u:GetOwner() == me then
                                        local info = GameInfo.Units[u:GetType()]
                                        if isFighter(info) then
                                            -- pcall's first return is its status: read the value.
                                            local ok, crossing = pcall(function()
                                                return cityPlot:IsRiverCrossingToPlot(Map.GetPlot(ux, uy))
                                            end)
                                            print("  ATTACKER|" .. info.UnitType .. "|" .. u:GetID()
                                                .. "|" .. ux .. "," .. uy
                                                .. "|dist:" .. Map.GetPlotDistance(ux, uy, cx, cy)
                                                .. "|river:" .. tostring(ok and crossing or false))
                                        end
                                    end
                                end
                            end
                        end
                    end
                end
            end
        end)
    end
end
print("---END---")
