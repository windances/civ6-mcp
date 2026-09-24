-- Read-only. The identity-conversion enum, and what the losing branch can name.
--
-- `IdentityConversionOutcome` resolves in the InGame state (the previous probe printed
-- "2/GAINING_LOYALTY"), so the adapter can report the game's own word for the outcome instead of
-- a numeric we would have to hardcode. Print every member so the fallback map can be written down,
-- and check that GetPotentialTransferPlayer() is callable here - it is what the game's loyalty
-- warning uses to say *who* takes the city (CityBannerManager.lua:2358).
for k, v in pairs(IdentityConversionOutcome) do
    print("ENUM|" .. tostring(k) .. "=" .. tostring(v))
end

local me = Game.GetLocalPlayer()
for _, c in Players[me]:GetCities():Members() do
    local ok, transfer = pcall(function()
        return c:GetCulturalIdentity():GetPotentialTransferPlayer()
    end)
    local who = "n/a"
    if ok and transfer and transfer >= 0 then
        local okname, nm = pcall(function()
            return Locale.Lookup(PlayerConfigurations[transfer]:GetCivilizationDescription())
        end)
        who = tostring(transfer) .. "/" .. (okname and nm or "?")
    end
    print("TRANSFER|" .. c:GetID() .. "|ok:" .. tostring(ok) .. "|" .. who)
    break
end
