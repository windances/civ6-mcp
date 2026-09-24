-- Read-only. Settle whether an attack from (54,40) onto (53,40) crosses a river.
--
-- Two measurements of the same call disagreed: a probe answered true, the estimate's own injected
-- debug line answered false. This asks the same call three times in one chunk (flakiness), the
-- reverse direction, the plots' own river-edge flags (which edge the river is on), and whether the
-- game exposes a combat preview to appeal to - the only authority above both of them.
local p53 = Map.GetPlot(53, 40)
local p54 = Map.GetPlot(54, 40)

for i = 1, 3 do
    print("CALL" .. i .. "|53to54:" .. tostring(p53:IsRiverCrossingToPlot(p54))
        .. "|54to53:" .. tostring(p54:IsRiverCrossingToPlot(p53)))
end

local function flagList(p)
    local out = {}
    for _, d in ipairs({ "W", "NW", "NE" }) do
        local fn = p["Is" .. d .. "OfRiver"]
        if type(fn) == "function" then
            local ok, v = pcall(fn, p)
            if ok and v then out[#out + 1] = d end
        end
    end
    return (#out > 0) and table.concat(out, ",") or "-"
end

print("FLAGS|53,40|" .. flagList(p53) .. "|river:" .. tostring(p53:IsRiver()))
print("FLAGS|54,40|" .. flagList(p54) .. "|river:" .. tostring(p54:IsRiver()))

-- Which plots are the neighbours of (54,40)? The NW edge is the one carrying a river.
for dx = -1, 1 do
    for dy = -1, 1 do
        local nx, ny = 54 + dx, 40 + dy
        if (dx ~= 0 or dy ~= 0) and Map.GetPlot(nx, ny)
            and Map.GetPlotDistance(54, 40, nx, ny) == 1 then
            print("NEIGH|54,40|" .. nx .. "," .. ny)
        end
    end
end

print("CM|" .. tostring(type(CombatManager)))
if type(CombatManager) == "table" then
    local names = {}
    for k, v in pairs(CombatManager) do
        if type(v) == "function" then names[#names + 1] = k end
    end
    table.sort(names)
    print("CMFN|" .. table.concat(names, ","))
end
