-- Read-only. Did a Corps actually form? Lists every land-combat unit with its military formation
-- (0 = single, 1 = corps, 2 = army on this build) and the total count, so the answer does not
-- depend on which unit type the previous run happened to print.
local me = Game.GetLocalPlayer()
local n, formed = 0, 0
for _, u in Players[me]:GetUnits():Members() do
    local info = GameInfo.Units[u:GetType()]
    if info and info.FormationClass == "FORMATION_CLASS_LAND_COMBAT" then
        n = n + 1
        local f = "?"
        pcall(function() f = tostring(u:GetMilitaryFormation()) end)
        if f ~= "0" and f ~= "?" then formed = formed + 1 end
        print("UNIT|" .. info.UnitType .. "#" .. u:GetID() .. "@" .. u:GetX() .. "," .. u:GetY()
            .. "|formation:" .. f .. "|base_cs:" .. tostring(info.Combat))
    end
end
print("TOTAL|" .. n .. "|in_formation:" .. formed)
