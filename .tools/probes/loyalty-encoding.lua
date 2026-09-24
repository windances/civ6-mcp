-- Read-only. Why does the game's loyalty advice reach us as mojibake?
--
-- Hypothesis: `gsub("%c", " ")` is not locale-neutral. Both the C locale and CP1252 treat
-- 0x81 0x8D 0x8F 0x90 0x9D as control codes, and every CJK character is a 3-byte UTF-8 sequence
-- drawn from 0x80-0xBF in its tail bytes - so `%c` eats one byte out of some characters and
-- leaves the rest, which the client then decodes as invalid UTF-8 ("errors=replace" -> U+FFFD).
--
-- Three variants of the same string, byte-counted, settle it:
--   RAW  what the game hands us
--   PCT  the current sanitiser             gsub("%c", " ")
--   SAFE the proposed sanitiser            only TAB/LF/CR, built with string.char so no escape
--                                          can be misread as a pattern class
local me = Game.GetLocalPlayer()

local function high(s)
    local n = 0
    for i = 1, #s do
        if s:byte(i) >= 128 then n = n + 1 end
    end
    return n
end

local sep = "[" .. string.char(9) .. string.char(10) .. string.char(13) .. "]"

for _, c in Players[me]:GetCities():Members() do
    local raw = ""
    pcall(function() raw = Locale.Lookup(c:GetLoyaltyAdvice()) end)
    raw = tostring(raw)
    local pct = raw:gsub("%c", " ")
    local safe = raw:gsub(sep, " ")
    print("ADVICE|" .. c:GetID() .. "|len:" .. #raw .. "," .. #pct .. "," .. #safe
        .. "|high:" .. high(raw) .. "," .. high(pct) .. "," .. high(safe)
        .. "|pct_removed:" .. (#raw - #pct) .. "|safe_removed:" .. (#raw - #safe))
end

-- And the loyalty outcome, which the countdown has to be read together with:
-- DLC/Expansion2/UI/CityBanners/CityBannerManager.lua:2355-2357 shows the warning only when
--   eOutcome == IdentityConversionOutcome.LOSING_LOYALTY and nTurns < 20
-- so GetTurnsToConversion() is a revolt countdown *only* while losing; while gaining it is the
-- count of turns until the pool is full.
for _, c in Players[me]:GetCities():Members() do
    local loy, turns, outcome, name = -1, -1, "?", "?"
    pcall(function()
        local cult = c:GetCulturalIdentity()
        loy = cult:GetLoyalty()
        turns = cult:GetTurnsToConversion()
        outcome = cult:GetConversionOutcome()
        local enumer = "unresolved"
        pcall(function()
            for k, v in pairs(IdentityConversionOutcome) do
                if v == outcome then enumer = k end
            end
        end)
        outcome = tostring(outcome) .. "/" .. enumer
        name = Locale.Lookup(c:GetName())
    end)
    local per_turn = -1
    pcall(function() per_turn = c:GetCulturalIdentity():GetLoyaltyPerTurn() end)
    print("OUTCOME|" .. c:GetID() .. "|" .. name .. "|loyalty:" .. string.format("%.1f", loy)
        .. "|per_turn:" .. string.format("%.1f", per_turn)
        .. "|turns:" .. turns .. "|outcome:" .. outcome)
end
