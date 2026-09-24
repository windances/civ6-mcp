-- Read-only. Which unit does an estimate actually resolve, and does the river call really answer
-- true for it?
--
-- `--estimate 1310724 53 40` printed `Modifiers: flank +6` with attCS 34 = 28 + 6, i.e. no river
-- penalty, while a probe using the same call (`tgtPlot:IsRiverCrossingToPlot(attPlot)`) answered
-- true for that pair. One of the two assumptions is wrong: either the query resolves a different
-- unit than the id suggests, or the call's answer depends on the direction of the arguments.
local me = Game.GetLocalPlayer()
local TARGET_X, TARGET_Y = 53, 40
local tgtPlot = Map.GetPlot(TARGET_X, TARGET_Y)

print("TARGET|" .. TARGET_X .. "," .. TARGET_Y
    .. "|isRiver:" .. tostring(tgtPlot:IsRiver())
    .. "|feature:" .. tostring(tgtPlot:GetFeatureType())
    .. "|terrain:" .. tostring(tgtPlot:GetTerrainType()))

for _, u in Players[me]:GetUnits():Members() do
    local info = GameInfo.Units[u:GetType()]
    if info and info.UnitType == "UNIT_HEAVY_CHARIOT" then
        local ux, uy = u:GetX(), u:GetY()
        local attPlot = Map.GetPlot(ux, uy)
        local fwd, err = pcall(function() return tgtPlot:IsRiverCrossingToPlot(attPlot) end)
        local back = pcall(function() return attPlot:IsRiverCrossingToPlot(tgtPlot) end)
        local canCross = pcall(function() return attPlot:IsRiverCrossingToPlot(tgtPlot) end)
        print("CHARIOT|id:" .. u:GetID()
            .. "|" .. ux .. "," .. uy
            .. "|hp:" .. (u:GetMaxDamage() - u:GetDamage())
            .. "|dist:" .. Map.GetPlotDistance(ux, uy, TARGET_X, TARGET_Y)
            .. "|tgt_to_att:" .. tostring(fwd)
            .. "|att_to_tgt:" .. tostring(back)
            .. "|err:" .. tostring(type(err) == "string" and err:sub(1, 30) or "none"))
    end
end

-- And what the estimate's own unit lookup would see, by id and by index into the member list.
local i = 0
for _, u in Players[me]:GetUnits():Members() do
    i = i + 1
    if i <= 3 or u:GetID() == 1310724 then
        local info = GameInfo.Units[u:GetType()]
        print("MEMBER|index:" .. i .. "|id:" .. u:GetID()
            .. "|" .. tostring(info and info.UnitType or "?"))
    end
end
