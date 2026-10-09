"""Units domain —Lua builders and parsers."""

from __future__ import annotations

from civ_mcp.lua._helpers import (
    _LUA_RES_VISIBLE,
    SENTINEL,
    _bail,
    _bail_lua,
    _lua_get_unit,
    _lua_get_unit_gamecore,
)
from civ_mcp.lua.models import (
    BuilderInfo,
    BuilderTask,
    CaptureReadiness,
    CombatEstimate,
    PathingEstimate,
    Reinforcement,
    ReligiousSighting,
    StagingOption,
    StagingPlan,
    StagingRingTile,
    StagingUnit,
    SiegePosture,
    ThreatInfo,
    UnitInfo,
)


def build_units_query() -> str:
    """InGame context: lists all units with upgrade and builder improvement info."""
    return """
local id = Game.GetLocalPlayer()
for i, u in Players[id]:GetUnits():Members() do
    local x, y = u:GetX(), u:GetY()
    if x ~= -9999 then
        local uid = u:GetID()
        local entry = GameInfo.Units[u:GetType()]
        local ut = entry and entry.UnitType or "UNKNOWN"
        local nm = Locale.Lookup(u:GetName())
        local cs = entry and entry.Combat or 0
        local rs = entry and entry.RangedCombat or 0
        -- A siege unit attacks a city with its Bombard strength and has RangedCombat 0
        -- (UNIT_CATAPULT: CS 25, RS 0, Bombard 35, Range 2). Testing RangedCombat alone leaves it
        -- out of the target scan entirely - its range reads 1 and its target list stays empty, so
        -- nothing downstream can see what a Catapult is actually able to shoot (live T107).
        local bomb = entry and entry.Bombard or 0
        local charges = u:GetBuildCharges() or 0
        local gp = u:GetGreatPerson()
        if gp then
            local ok_gp, gp_charges = pcall(function() return gp:GetActionCharges() end)
            if ok_gp and gp_charges and gp_charges > 0 then charges = gp_charges end
            if charges == 0 then
                -- Cultural GPs (Writers/Artists/Musicians) return 0 from
                -- GetActionCharges(). Fall back to the individual definition.
                pcall(function()
                    local indIdx = gp:GetIndividual()
                    for ind in GameInfo.GreatPersonIndividuals() do
                        if ind.Index == indIdx then
                            charges = ind.ActionCharges or 0
                            break
                        end
                    end
                end)
            end
        end
        if charges == 0 then
            local ok_sp, sp = pcall(function() return u:GetSpreadCharges() end)
            if ok_sp and sp and sp > 0 then charges = sp end
        end
        local relName = ""
        local ok_r, rIdx = pcall(function() return u:GetReligionType() end)
        if ok_r and rIdx and rIdx >= 0 then
            for row in GameInfo.Religions() do
                if row.Index == rIdx then relName = row.ReligionType; break end
            end
        end
        -- Scan for attackable enemies if unit has moves.
        -- A siege unit that is not also ranged (`bomb > 0 and rs == 0`, the predicate the action path
        -- refuses at `ERR:SIEGE_CANNOT_ATTACK_UNITS`) has **no legal unit target at all**: Catapults
        -- and Trebuchets attack cities and districts only. The hint used to list unit targets for them
        -- anyway - measured in attempt A2 at T55, where a Catapult ordered onto the listed Archer came
        -- back `ERR:SIEGE_CANNOT_ATTACK_UNITS`, and again at T66 where a Catapult was offered two
        -- Archers and a Heavy Chariot. `build_unused_attack_query` already excludes them and claims the
        -- two tests mirror each other, so the contradiction was in this scan.
        local targets = ""
        local siegeNoRanged = (bomb > 0 and rs == 0)
        -- A **melee land unit cannot attack a unit at sea** (manual:723), and the action path refuses
        -- it by name (`ERR:MELEE_CANNOT_ATTACK_AT_SEA`, the same `Domain` test). Listing it here is
        -- how a Barbarian Galley in our own harbour came back as an attackable target every turn
        -- (measured T95-T97 on the live branch), so the hint applies the same predicate.
        local iAmLandMelee = (rs == 0) and entry ~= nil and entry.Domain == "DOMAIN_LAND"
        if u:GetMovesRemaining() > 0 and (cs > 0 or rs > 0 or bomb > 0) and not siegeNoRanged then
            local rng = ((rs > 0 or bomb > 0) and (entry and entry.Range or 1)) or 1
            local tgtList = {}
            for dy = -rng, rng do
                for dx = -rng, rng do
                    local tx, ty = x + dx, y + dy
                    local d = Map.GetPlotDistance(x, y, tx, ty)
                    if d >= 1 and d <= rng then
                        local plotUnits = Map.GetUnitsAt(tx, ty)
                        if plotUnits then
                            for other in plotUnits:Units() do
                                local otherOwner = other:GetOwner()
                                if otherOwner ~= id and (otherOwner == 63 or Players[id]:GetDiplomacy():IsAtWarWith(otherOwner)) then
                                    -- LOS check for ranged units (d>1): verify the
                                    -- game engine agrees we can actually fire there.
                                    -- Melee (d==1) doesn't need LOS.
                                    local losOK = true
                                    if rs > 0 and d > 1 then
                                        local lp = {{}}
                                        lp[UnitOperationTypes.PARAM_X] = tx
                                        lp[UnitOperationTypes.PARAM_Y] = ty
                                        -- Guarded: `UnitManager` exists in the GameCore state but
                                        -- without CanStartOperation, and calling it there raised
                                        -- "function expected instead of nil" - live T122, the
                                        -- post-turn snapshot after Moscow was taken lost the whole
                                        -- unit list to this one line. Without the engine check the
                                        -- LOS filter is skipped rather than the query failing.
                                        local okL, los = pcall(function()
                                            return UnitManager.CanStartOperation(
                                                u, UnitOperationTypes.RANGE_ATTACK, nil, lp)
                                        end)
                                        losOK = (okL and los) and true or (not okL)
                                    end
                                    local otherInfo = GameInfo.Units[other:GetType()]
                                    local targetAtSea = otherInfo ~= nil
                                        and otherInfo.Domain == "DOMAIN_SEA"
                                    if iAmLandMelee and targetAtSea then losOK = false end
                                    if losOK then
                                        local eInfo = GameInfo.Units[other:GetType()]
                                        local eName = eInfo and eInfo.UnitType or "UNKNOWN"
                                        local eHP = other:GetMaxDamage() - other:GetDamage()
                                        table.insert(tgtList, eName .. "@" .. tx .. "," .. ty .. "(" .. eHP .. "hp)")
                                    end
                                end
                            end
                        end
                    end
                end
            end
            if #tgtList > 0 then targets = table.concat(tgtList, ";") end
        end
        -- NOTE: promotion detection is intentionally omitted here.
        -- GetExperiencePoints() >= GetExperienceForNextLevel() stays true after
        -- SetPromotion() (level and XP are not consumed), so any mid-turn check
        -- fires one turn early AND causes double-promotions when end_turn's
        -- authoritative GameCore CanPromote check also fires.
        -- All promotion handling is routed through the end_turn blocker (which
        -- uses CanPromote in GameCore —the only correct check).
        local promo = "0"
        -- Upgrade info (InGame only: CanStartCommand)
        local canUp, upName, upCost = "0", "", "0"
        local ok1, _ = pcall(function()
            if UnitManager.CanStartCommand(u, UnitCommandTypes.UPGRADE, nil, true) then
                canUp = "1"
                local c2 = u:GetUpgradeCost()
                if c2 then upCost = tostring(c2) end
                if entry and entry.UpgradeUnitCollection then
                    for _, row in ipairs(entry.UpgradeUnitCollection) do
                        if row.UpgradeUnit then upName = row.UpgradeUnit end
                        break
                    end
                end
            end
        end)
        -- Builder improvement advisor (InGame only: CanStartOperation)
        local validImps = ""
        if ut == "UNIT_BUILDER" and u:GetMovesRemaining() > 0 then
            local plot = Map.GetPlot(x, y)
            if plot and plot:GetOwner() == id then
                local impList = {}
                for imp in GameInfo.Improvements() do
                    if imp.Buildable and not imp.TraitType then
                        local bParams = {}
                        bParams[UnitOperationTypes.PARAM_X] = x
                        bParams[UnitOperationTypes.PARAM_Y] = y
                        bParams[UnitOperationTypes.PARAM_IMPROVEMENT_TYPE] = imp.Hash
                        local ok2, _ = pcall(function()
                            if UnitManager.CanStartOperation(u, UnitOperationTypes.BUILD_IMPROVEMENT, nil, bParams) then
                                table.insert(impList, imp.ImprovementType)
                            end
                        end)
                    end
                end
                if #impList > 0 then validImps = table.concat(impList, ";") end
            end
        end
        -- Military Engineer advisor (BUILD_ROUTE + fort/airstrip)
        if ut == "UNIT_MILITARY_ENGINEER" and u:GetMovesRemaining() > 0 then
            local meList = {}
            pcall(function()
                local opRow = GameInfo.UnitOperations["UNITOPERATION_BUILD_ROUTE"]
                if opRow then
                    local rp = {}
                    rp[UnitOperationTypes.PARAM_X] = x
                    rp[UnitOperationTypes.PARAM_Y] = y
                    if UnitManager.CanStartOperation(u, opRow.Hash, nil, rp) then
                        table.insert(meList, "BUILD_ROUTE")
                    end
                end
            end)
            local plot = Map.GetPlot(x, y)
            if plot and plot:GetOwner() == id then
                for imp in GameInfo.Improvements() do
                    if imp.Buildable and not imp.TraitType then
                        pcall(function()
                            local bp = {}
                            bp[UnitOperationTypes.PARAM_X] = x
                            bp[UnitOperationTypes.PARAM_Y] = y
                            bp[UnitOperationTypes.PARAM_IMPROVEMENT_TYPE] = imp.Hash
                            if UnitManager.CanStartOperation(u, UnitOperationTypes.BUILD_IMPROVEMENT, nil, bp) then
                                table.insert(meList, imp.ImprovementType)
                            end
                        end)
                    end
                end
            end
            if #meList > 0 then validImps = table.concat(meList, ";") end
        end
        -- What the unit is *doing*, read exactly the way the game's own unit panel reads it
        -- (`Base/Assets/UI/Panels/UnitPanel.lua:4054-4062`): `UnitManager.GetActivityType`, compared
        -- against the engine's own `ActivityTypes` table. Two facts make this three fields rather
        -- than one - **fortified is not an activity at all** (it is `GetFortifyTurns() > 0` with the
        -- activity not AWAKE), and `IsReadyToMove()` is the game's own answer for whether the unit
        -- can still act. Without them, a **sleeping** unit is indistinguishable from a unit nobody
        -- has ordered yet: both report full movement and neither is named by any report.
        local actName, fortTurns, ready = "?", 0, true
        pcall(function()
            fortTurns = u:GetFortifyTurns() or 0
            ready = u:IsReadyToMove() and true or false
            local at = UnitManager.GetActivityType(u)
            for actKey, actValue in pairs(ActivityTypes) do
                if actValue == at then actName = actKey break end
            end
        end)
        print(uid .. "|" .. (uid % 65536) .. "|" .. nm .. "|" .. ut .. "|" .. x .. "," .. y .. "|" .. u:GetMovesRemaining() .. "/" .. u:GetMaxMoves() .. "|" .. (u:GetMaxDamage() - u:GetDamage()) .. "/" .. u:GetMaxDamage() .. "|" .. cs .. "|" .. rs .. "|" .. charges .. "|" .. targets .. "|" .. promo .. "|" .. canUp .. "|" .. upName .. "|" .. upCost .. "|" .. validImps .. "|" .. relName .. "|" .. actName .. "|" .. fortTurns .. "|" .. (ready and 1 or 0))
    end
end
print("{SENTINEL}")
""".replace("{SENTINEL}", SENTINEL)


def build_move_unit(unit_index: int, target_x: int, target_y: int) -> str:
    return f"""
{_lua_get_unit(unit_index)}
if unit:GetMovesRemaining() <= 0 then
    {_bail("ERR:NO_MOVES|Unit has no movement points remaining this turn. Use skip or wait until next turn.")}
end
if not UnitManager.CanStartOperation(unit, UnitOperationTypes.MOVE_TO, nil, true) then
    {_bail("ERR:CANNOT_MOVE|Unit cannot move (invalid state)")}
end
-- Pre-check: stacking conflict at target tile
local unitInfo = GameInfo.Units[unit:GetType()]
local isCivilian = (unitInfo and unitInfo.FormationClass == "FORMATION_CLASS_CIVILIAN")
local tgtUnits = Map.GetUnitsAt({target_x}, {target_y})
if tgtUnits then
    for other in tgtUnits:Units() do
        if other:GetOwner() == me then
            local otherInfo = GameInfo.Units[other:GetType()]
            local otherCivilian = (otherInfo and otherInfo.FormationClass == "FORMATION_CLASS_CIVILIAN")
            if isCivilian == otherCivilian then
                local otherName = otherInfo and otherInfo.UnitType or "unit"
                {_bail_lua(f'"ERR:STACKING_CONFLICT|Friendly " .. otherName .. " already on ({target_x},{target_y}). Cannot stack same formation class."')}
            end
        end
    end
end
local fromX, fromY = unit:GetX(), unit:GetY()
local params = {{}}
params[UnitOperationTypes.PARAM_X] = {target_x}
params[UnitOperationTypes.PARAM_Y] = {target_y}
-- Add ATTACK modifier if a hostile unit - or an enemy city - is on the target tile (needed for
-- civilian capture, and for taking a city). Map.GetUnitsAt only sees units, so an enemy city
-- with no garrison in it looked like an ordinary tile: the move went out without the ATTACK
-- modifier and the game refused it ("enemy territory but movement still blocked"), which is how
-- a city sitting at `city hp: 0/200` stayed untaken. Moving a melee unit onto a city whose HP
-- pool is empty is the capture.
local hasHostile = false
if tgtUnits then
    for other in tgtUnits:Units() do
        if other:GetOwner() ~= me then hasHostile = true end
    end
end
if not hasHostile then
    pcall(function()
        local c = Cities.GetCityInPlot({target_x}, {target_y})
        if c and c:GetOwner() ~= me then hasHostile = true end
    end)
end
if hasHostile then
    params[UnitOperationTypes.PARAM_MODIFIERS] = UnitOperationMoveModifiers.ATTACK
end
UnitManager.RequestOperation(unit, UnitOperationTypes.MOVE_TO, params)
local tag = hasHostile and "OK:CAPTURE_MOVE|" or "OK:MOVING_TO|"
print(tag .. {target_x} .. "," .. {target_y} .. "|from:" .. fromX .. "," .. fromY)
print("{SENTINEL}")
"""


def build_unit_position_query(
    unit_index: int,
    move_target_x: int | None = None,
    move_target_y: int | None = None,
) -> str:
    """GameCore: read a unit's current position.

    When *move_target_x/y* are provided, also diagnoses why a blocked move
    failed (water, mountain, foreign border) so the caller doesn't need a
    second round-trip.
    """
    diag_block = ""
    if move_target_x is not None and move_target_y is not None:
        diag_block = f"""
-- Diagnose blocked move target
pcall(function()
    local plot = Map.GetPlot({move_target_x}, {move_target_y})
    if not plot then print("DIAG|UNKNOWN|tile does not exist"); return end
    if plot:IsWater() then
        local hasShip = false
        pcall(function()
            local tech = GameInfo.Technologies["TECH_SHIPBUILDING"]
            if tech then hasShip = Players[me]:GetTechs():HasTech(tech.Index) end
        end)
        if hasShip then print("DIAG|WATER_OK|water tile (can embark)")
        else print("DIAG|WATER|water tile - land units need Shipbuilding tech to embark") end
    elseif plot:IsMountain() then
        print("DIAG|MOUNTAIN|impassable mountain")
    elseif plot:IsImpassable() then
        print("DIAG|IMPASSABLE|impassable terrain (ice or natural wonder)")
    else
        local owner = plot:GetOwner()
        if owner >= 0 and owner ~= me then
            local atWar = false
            pcall(function() atWar = Players[me]:GetDiplomacy():IsAtWarWith(owner) end)
            if atWar then
                print("DIAG|UNKNOWN|tile is enemy territory but movement still blocked - check path")
            else
                local civName = "player " .. owner
                pcall(function()
                    local cfg = PlayerConfigurations[owner]
                    civName = cfg and Locale.Lookup(cfg:GetCivilizationShortDescription()) or civName
                end)
                local isMajor = true
                pcall(function() isMajor = Players[owner]:IsMajor() end)
                if isMajor then
                    print("DIAG|BORDER|foreign territory (" .. civName .. ") - need Open Borders via propose_trade")
                else
                    print("DIAG|BORDER_CS|city-state territory (" .. civName .. ") - need suzerainty or Open Borders")
                end
            end
        else
            print("DIAG|UNKNOWN|tile appears passable - path may be blocked by intermediate tiles")
        end
    end
end)
"""
    return f"""
local me = Game.GetLocalPlayer()
local u = Players[me]:GetUnits():FindID({unit_index})
if u then
    print("POS|" .. u:GetX() .. "|" .. u:GetY())
    -- Whether the tile we ended on holds a city, and whose it is. A move onto an enemy city at
    -- 0 HP *is* the capture, and the move response used to end at `now_at:54,40` with no word for
    -- it: live T122 a Heavy Chariot took Moscow that way and the caller had to infer the capture
    -- from the city list. One extra line is the difference between "moved" and "took the city".
    pcall(function()
        local c = Cities.GetCityInPlot(u:GetX(), u:GetY())
        if c then
            print("ONCITY|" .. c:GetID() .. "|owner:" .. c:GetOwner()
                .. "|" .. Locale.Lookup(c:GetName()):gsub("|", "/"))
        end
    end)
else
    print("POS|GONE")
end
{diag_block}print("{SENTINEL}")
"""


def build_attack_unit(unit_index: int, target_x: int, target_y: int) -> str:
    return f"""
{_lua_get_unit(unit_index)}
local ux, uy = unit:GetX(), unit:GetY()
local dist = Map.GetPlotDistance(ux, uy, {target_x}, {target_y})
-- Find hostile unit on target tile (prefer military over civilian)
local enemy = nil
local enemyName = "unknown"
local tgtUnits = Map.GetUnitsAt({target_x}, {target_y})
if tgtUnits then
    local fallback = nil
    local fallbackName = "unknown"
    for other in tgtUnits:Units() do
        if other:GetOwner() ~= me then
            local eInfo = GameInfo.Units[other:GetType()]
            local eName = eInfo and eInfo.UnitType or "UNKNOWN"
            local eCombat = eInfo and eInfo.Combat or 0
            if eCombat > 0 then
                enemy = other
                enemyName = eName
                break
            elseif fallback == nil then
                fallback = other
                fallbackName = eName
            end
        end
    end
    if enemy == nil and fallback then enemy = fallback; enemyName = fallbackName end
end
-- A city centre is a legal target with or without a garrison, but Map.GetUnitsAt only ever sees
-- units: an enemy city that is momentarily empty used to answer ERR:NO_ENEMY, and the assault
-- stalled on a city that had already been broken. Live, Moscow sat at `city hp: 0/200` from T120
-- while every attack returned NO_ENEMY, healed about twenty points a turn back to 120/200, and
-- the campaign was abandoned; the same city fell in four turns once a human attacked the tile
-- from the game UI. Cities.GetCityInPlot is the API the game's own UI uses.
--
-- The resolution is the *first* thing that happens, and it wins over a unit on the tile: a city
-- tile is attacked as a city, because the game routes an attack on that tile to the city pool and
-- the unit inside is not separately attackable. Live T107: two Archers and a Catapult fired at
-- Moscow and put 76 points into the garrison ARCHER and 11 into the 200-point pool - the doctrine
-- says exactly why that is wasted ("a garrison inside takes no damage while the city is attacked
-- and dies only with the city"). The plot must be the city's *own* tile, not merely inside its
-- territory, or an attack on a unit standing on a farm would be redirected to the city.
local targetCity = nil
local cityOwner = -1
local targetIsCity = false
pcall(function()
    local c = Cities.GetCityInPlot({target_x}, {target_y})
    if c and c:GetX() == {target_x} and c:GetY() == {target_y} then
        targetCity = c
        cityOwner = c:GetOwner()
        targetIsCity = true
        -- Named here, not further down: the not-at-war message below quotes it, and a city
        -- that is out of reach should be named in the refusal (live T102 it read "unknown").
        pcall(function() enemyName = Locale.Lookup(c:GetName()):gsub("|", "/") end)
    end
end)
if targetCity ~= nil then enemy = nil end
if enemy == nil and targetCity == nil then
    {_bail(f"ERR:NO_ENEMY|No hostile unit or city at ({target_x},{target_y})")}
end
-- Check diplomatic status —can only attack units you're at war with (barbarians always attackable)
local enemyOwner = enemy and enemy:GetOwner() or cityOwner
if enemyOwner ~= 63 then
    local pDiplo = Players[me]:GetDiplomacy()
    if not pDiplo:IsAtWarWith(enemyOwner) then
        local ownerCfg = PlayerConfigurations[enemyOwner]
        local ownerName = ownerCfg and Locale.Lookup(ownerCfg:GetCivilizationDescription()) or ("player " .. enemyOwner)
        {_bail_lua('"ERR:NOT_AT_WAR|Cannot attack " .. enemyName .. " —you are at peace with " .. ownerName .. ". Declare war first or target a different unit."')}
    end
end
local unitInfo = GameInfo.Units[unit:GetType()]
local attRS = unitInfo and unitInfo.RangedCombat or 0
local attBombard = unitInfo and unitInfo.Bombard or 0
local attRange = unitInfo and unitInfo.Range or 1
-- The target's domain decides whether a melee attack is legal at all. manual:723 (MELEE UNITS):
-- "Melee units are land units which can attack enemies in adjacent land hexes. **They cannot attack
-- enemies at sea**, nor can they attack enemies more than one hex away." The engine still accepts the
-- order, resolves it as `MELEE_ATTACK` and deals nothing, so the fallback further down silently
-- produced a no-op the agent read as a hit. Measured T222-T237 on this branch: seven melee attacks on
-- Dutch Caravels, the enemy's HP identical every time (57 -> 57, 100 -> 100, seventeen turns running)
-- and two of our units sunk while standing in the water. The same anomaly was already written down in
-- three retired task files (018 at T216, 019 and 021 at T225) and never turned into a refusal.
local enemyIsSea = false
if enemy ~= nil then
    local enemyInfo = GameInfo.Units[enemy:GetType()]
    enemyIsSea = enemyInfo ~= nil and enemyInfo.Domain == "DOMAIN_SEA"
end
local attackerIsLand = unitInfo ~= nil and unitInfo.Domain == "DOMAIN_LAND"
-- A siege unit cannot attack a **unit**. The classification below only reads a Bombard as ranged when
-- the target is a city, so an order against a unit fell through to the melee branch and the Catapult
-- WALKED toward the target: measured live T140, one whole turn lost and a misleading STOPPED_SHORT
-- back. The right answer against a unit is a ranged unit, so refuse it here, by name.
if enemy ~= nil and attBombard > 0 and attRS == 0 then
    {_bail_lua('"ERR:SIEGE_CANNOT_ATTACK_UNITS|" .. enemyName .. " is a unit, and a siege unit cannot attack units - Catapults and Trebuchets attack cities and districts only. Use a ranged unit (Crossbowman, RS 40) against units, or target the city tile it stands on."')}
end
local enemyHP = 0
local enemyMaxHP = 0
if enemy then
    enemyHP = enemy:GetMaxDamage() - enemy:GetDamage()
    enemyMaxHP = enemy:GetMaxDamage()
else
    -- What is being attacked, and by which number: a unit's HP, or the city's own HP pool (the
    -- garrison pool of the city centre district - walls are a separate pool, damaged first).
    pcall(function() enemyName = Locale.Lookup(targetCity:GetName()):gsub("|", "/") end)
    pcall(function()
        local ccIdx = GameInfo.Districts["DISTRICT_CITY_CENTER"].Index
        for _, d in targetCity:GetDistricts():Members() do
            if d:GetType() == ccIdx then
                enemyMaxHP = d:GetMaxDamage(DefenseTypes.DISTRICT_GARRISON) or 0
                enemyHP = enemyMaxHP - (d:GetDamage(DefenseTypes.DISTRICT_GARRISON) or 0)
                break
            end
        end
    end)
end
local myHP = unit:GetMaxDamage() - unit:GetDamage()
local params = {{}}
params[UnitOperationTypes.PARAM_X] = {target_x}
params[UnitOperationTypes.PARAM_Y] = {target_y}
-- Determine attack type. A siege unit's attack on a city is its **Bombard** strength and its
-- RangedCombat is 0 (UNIT_CATAPULT: CS 25, RS 0, Bombard 35, Range 2), so a classification that
-- tests RangedCombat alone reads a Catapult as melee: the estimate prints "Melee", the attack path
-- walks it toward the city and reports STOPPED_SHORT when the movement runs out, and the blow that
-- does land is resolved as a melee attack that takes retaliation. Live T107: a Catapult standing
-- two tiles from Moscow was refused `RANGE_ATTACK` and spent the turn walking instead.
-- (unitInfo/attRS/attBombard/attRange are read above, before the siege-versus-unit refusal.)
local isRanged = (attRS > 0 or (attBombard > 0 and targetIsCity)) and dist <= attRange
if not isRanged then
    isRanged = UnitManager.CanStartOperation(unit, UnitOperationTypes.RANGE_ATTACK, nil, params)
end
local isAir = (not isRanged) and UnitManager.CanStartOperation(unit, UnitOperationTypes.AIR_ATTACK, nil, params)
if isRanged then
    if unit:GetMovesRemaining() <= 0 then
        {_bail("ERR:NO_MOVES|Unit has no movement points for ranged attack. Ranged attacks require movement. Move and attack on separate turns, or attack before moving.")}
    end
    local rng = unitInfo and unitInfo.Range or 1
    if dist > rng then
        {_bail_lua('"ERR:OUT_OF_RANGE|Target at distance " .. dist .. " but range is " .. rng .. ". Move closer first."')}
    end
    -- LOS check: CanStartOperation with target params is authoritative;
    -- GetOperationTargets returns empty for some valid targets (naval units, etc.)
    local losParams = {{}}
    losParams[UnitOperationTypes.PARAM_X] = {target_x}
    losParams[UnitOperationTypes.PARAM_Y] = {target_y}
    local canRanged = UnitManager.CanStartOperation(unit, UnitOperationTypes.RANGE_ATTACK, nil, losParams)
    if canRanged then
        UnitManager.RequestOperation(unit, UnitOperationTypes.RANGE_ATTACK, params)
        local kind = targetIsCity and " (city)" or ""
        print("OK:RANGE_ATTACK|target:" .. enemyName .. kind .. " at ({target_x},{target_y})|pre_hp:" .. enemyHP .. "/" .. enemyMaxHP .. "|your HP:" .. myHP .. "|range:" .. rng .. " dist:" .. dist)
        print("{SENTINEL}"); return
    elseif dist <= 1 then
        -- Ranged failed at melee range: fall through to melee attack below
        isRanged = false
    else
        {_bail_lua(f'"ERR:NO_LOS|Cannot ranged-attack target at ({target_x},{target_y}) from (" .. ux .. "," .. uy .. "). LOS blocked or unit already attacked this turn."')}
    end
end
-- A melee land unit versus a unit at sea is not a weak attack, it is not an attack at all
-- (manual:723). Refuse it by name and point at the manual, instead of letting the engine accept a
-- command that resolves as a hit and deals nothing. This is also the branch the old ranged-at-d1
-- fallback above fell into: `CanStartOperation(RANGE_ATTACK)` answers false against a ship at
-- distance 1, and the fall-through turned a legal shot into an illegal no-op.
if (not isRanged) and enemyIsSea and attackerIsLand then
    {_bail_lua('"ERR:MELEE_CANNOT_ATTACK_AT_SEA|" .. enemyName .. " is at sea, and this order resolved as a melee attack: melee land units cannot attack enemies at sea (manual:723). Ranged units always use ranged combat, even when adjacent (manual:725) - fire from two tiles away, or use a naval unit (task 026). Moving a melee unit into the water to reach it only feeds their ships."')}
end
if isAir then
    -- Air units (jet bombers, jet fighters, bombers, fighters): use AIR_ATTACK operation.
    -- Combat resolves asynchronously in the UI so post-combat HP reads may be stale.
    local rng = unitInfo and unitInfo.Range or 1
    if dist > rng then
        {_bail_lua('"ERR:OUT_OF_RANGE|Target at distance " .. dist .. " but air range is " .. rng .. ". Rebase closer first."')}
    end
    UnitManager.RequestOperation(unit, UnitOperationTypes.AIR_ATTACK, params)
    print("OK:AIR_ATTACK|target:" .. enemyName .. " at ({target_x},{target_y})|pre_hp:" .. enemyHP .. "/" .. enemyMaxHP .. "|bomber HP:" .. myHP .. "|range:" .. rng .. " dist:" .. dist)
else
    -- Melee: let CanStartOperation be the authority on adjacency/validity.
    -- Map.GetPlotDistance can misreport distance on offset hex grids, so we
    -- do not use it as a gate here —only as a diagnostic in the error message.
    local myCS = unitInfo and unitInfo.Combat or 0
    -- Movement check: melee attack requires movement points (ranged does not)
    if unit:GetMovesRemaining() <= 0 then
        {_bail("ERR:NO_MOVES|Unit has no movement points for melee attack. Melee requires movement to close distance. Wait until next turn.")}
    end
    -- ZOC check: if unit entered enemy ZOC this turn, it cannot attack until next turn.
    -- CanStartOperation returns true but RequestOperation silently queues for next turn.
    if unit:HasMovedIntoZOC() then
        {_bail_lua('"ERR:ZOC|Unit entered Zone of Control this turn —cannot attack until next turn. End turn and attack from current position next turn."')}
    end
    params[UnitOperationTypes.PARAM_MODIFIERS] = UnitOperationMoveModifiers.ATTACK
    if not UnitManager.CanStartOperation(unit, UnitOperationTypes.MOVE_TO, nil, params) then
        {_bail_lua('"ERR:ATTACK_BLOCKED|Cannot attack " .. enemyName .. " at ({target_x},{target_y}) (map dist=" .. dist .. "). Unit not adjacent or blocked by popup/diplomacy."')}
    end
    UnitManager.RequestOperation(unit, UnitOperationTypes.MOVE_TO, params)
    -- Verify unit reached adjacency (MOVE_TO resolves synchronously for movement)
    local newX, newY = unit:GetX(), unit:GetY()
    local newDist = Map.GetPlotDistance(newX, newY, {target_x}, {target_y})
    if newDist > 1 then
        print("ERR:STOPPED_SHORT|Unit moved to (" .. newX .. "," .. newY .. ") but could not reach target at ({target_x},{target_y}) —" .. newDist .. " tiles away. Movement exhausted by terrain. Try again next turn from closer position.")
        print("{SENTINEL}"); return
    end
    -- Try to read post-combat state (may fail if units moved/died)
    local myAfterHP = myHP
    local ok1, _ = pcall(function() myAfterHP = unit:GetMaxDamage() - unit:GetDamage() end)
    local enemyAfterHP = 0
    local enemyAlive = false
    if enemy then
        local ok2, _ = pcall(function()
            local d = enemy:GetDamage()
            if d ~= nil then enemyAfterHP = enemy:GetMaxDamage() - d; enemyAlive = true end
        end)
    else
        -- City target: re-read the city's own HP pool, and whether we are standing in the city
        -- now - a melee move onto a city whose HP pool is empty is how a city is taken.
        pcall(function()
            local ccIdx = GameInfo.Districts["DISTRICT_CITY_CENTER"].Index
            for _, d in targetCity:GetDistricts():Members() do
                if d:GetType() == ccIdx then
                    enemyAfterHP = (d:GetMaxDamage(DefenseTypes.DISTRICT_GARRISON) or 0)
                        - (d:GetDamage(DefenseTypes.DISTRICT_GARRISON) or 0)
                    enemyAlive = true
                    break
                end
            end
        end)
    end
    local label = targetIsCity and "city HP:" or "enemy HP:"
    local report = "OK:MELEE_ATTACK|target:" .. enemyName .. " at ({target_x},{target_y})"
    if enemyAlive then
        report = report .. "|" .. label .. enemyHP .. " -> " .. enemyAfterHP .. "/" .. enemyMaxHP
        if enemyAfterHP == enemyHP then
            -- Combat resolves asynchronously, so this read can still return the pre-attack damage.
            -- Measured 2026-09-29 in attempt A2: two landed melee attacks both answered
            -- "enemy HP:72 -> 72/100", the read right after agreed, and the target then went
            -- 72 -> 50 -> 20 -> dead over the next turns. The session read the unchanged pair as a
            -- silent failure, could not pass the pending-attack gate, and closed the turn with
            -- `skip_remaining_units(force=True)`, discarding a legal attack.
            report = report .. " (unchanged on this read - combat resolves asynchronously, so the hit may still have landed; read the target again before concluding it missed)"
        end
    else
        report = report .. "|" .. label .. enemyHP .. " -> KILLED"
    end
    report = report .. "|your HP:" .. myHP .. " -> " .. myAfterHP .. " CS:" .. myCS
    if targetIsCity and unit:GetX() == {target_x} and unit:GetY() == {target_y} then
        report = report .. "|CITY TAKEN - resolve keep/raze with city_action"
    end
    print(report)
end
print("{SENTINEL}")
"""


def build_attack_followup_query(target_x: int, target_y: int) -> str:
    """InGame context: get actual HP of units at target tile after combat.

    Also checks for city defenses (walls/garrison) at the target —when
    attacking a walled city, damage goes to walls first so the garrison
    unit's HP stays unchanged even though the attack succeeded.

    Runs in InGame context because enemy city district APIs
    (GetDistricts, GetMaxDamage) are not available in GameCore.
    """
    return f"""
local found = false
for i = 0, 63 do
    if Players[i] and Players[i]:IsAlive() then
        for _, u in Players[i]:GetUnits():Members() do
            if u:GetX() == {target_x} and u:GetY() == {target_y} then
                local hp = u:GetMaxDamage() - u:GetDamage()
                local entry = GameInfo.Units[u:GetType()]
                local name = entry and entry.UnitType or "UNKNOWN"
                print("UNIT|" .. name .. "|" .. hp .. "/" .. u:GetMaxDamage() .. "|owner:" .. i)
                found = true
            end
        end
        pcall(function()
            for _, c in Players[i]:GetCities():Members() do
                if c:GetX() == {target_x} and c:GetY() == {target_y} then
                    local ccIdx = GameInfo.Districts["DISTRICT_CITY_CENTER"].Index
                    for _, d in c:GetDistricts():Members() do
                        if d:GetType() == ccIdx then
                            pcall(function()
                                local wMax = d:GetMaxDamage(DefenseTypes.DISTRICT_OUTER) or 0
                                local wHP = wMax - (d:GetDamage(DefenseTypes.DISTRICT_OUTER) or 0)
                                local gMax = d:GetMaxDamage(DefenseTypes.DISTRICT_GARRISON) or 0
                                local gHP = gMax - (d:GetDamage(DefenseTypes.DISTRICT_GARRISON) or 0)
                                if wMax > 0 or gMax > 0 then
                                    print("CITY_DEF|wall:" .. wHP .. "/" .. wMax .. "|garrison:" .. gHP .. "/" .. gMax)
                                end
                            end)
                            break
                        end
                    end
                end
            end
        end)
    end
end
if not found then print("EMPTY") end
print("{SENTINEL}")
"""


def parse_blocked_diagnostic(lines: list[str]) -> str:
    """Extract human-readable block reason from diagnostic Lua output."""
    for line in lines:
        if line.startswith("DIAG|"):
            parts = line.split("|", 2)
            if len(parts) >= 3:
                return parts[2]
    return "unit did not move —impassable terrain, border, or no path"


def build_combat_estimate_query(unit_index: int, target_x: int, target_y: int) -> str:
    """InGame context: gather combat stats for damage estimation (no attack executed).

    Includes: base CS, promotions, fortification, terrain (hills, forest/jungle),
    river crossing, flanking bonus, and support bonus.
    """
    return f"""
{_lua_get_unit(unit_index)}
local ux, uy = unit:GetX(), unit:GetY()
local dist = Map.GetPlotDistance(ux, uy, {target_x}, {target_y})
local unitInfo = GameInfo.Units[unit:GetType()]
local attType = unitInfo and unitInfo.UnitType or "UNKNOWN"
local attCS = unitInfo and unitInfo.Combat or 0
local attRS = unitInfo and unitInfo.RangedCombat or 0
local attBombard = unitInfo and unitInfo.Bombard or 0
-- A city tile is a city target even when a unit is standing in it: the garrison is not separately
-- attackable, it takes no damage while the city is attacked, and what the estimate should describe
-- is the pool that actually moves. Live T107: an estimate that reasoned about the garrison ARCHER
-- read "~76 damage" while the attack put 76 into that unit and 11 into the city.
local tCityOnTile = nil
pcall(function()
    local c = Cities.GetCityInPlot({target_x}, {target_y})
    if c and c:GetX() == {target_x} and c:GetY() == {target_y} then tCityOnTile = c end
end)
-- A siege unit's city attack is its Bombard strength and its RangedCombat is 0 (UNIT_CATAPULT:
-- CS 25, RS 0, Bombard 35, Range 2), so a test on RangedCombat alone calls it melee.
--
-- **`dist <= attRange`, not `dist > 1`** (fixed 2026-10-02). Ranged units always use ranged combat,
-- even when adjacent (manual:725) - the attack path itself quotes that line - so a shot at distance 1
-- is a ranged attack. The old test mirrored the *fallback* branch in `build_attack_unit` (melee after
-- a refused ranged attempt) instead of its primary test, and every point-blank shot was estimated as
-- a melee attack: measured live T96-T97, an Archer and a Skirmisher firing at distance 1 both printed
-- `Combat Estimate (Melee)` with "Est damage to attacker: ~44" and "~302" and a
-- "WARNING: attacker likely dies!". Both resolved as `RANGE_ATTACK` and took no damage at all, so the
-- two numbers the estimate exists to give (the damage to the defender, and whether the attacker is
-- safe) were one wrong model's.
local attRange = (unitInfo and unitInfo.Range) or 1
local isRanged = (attRS > 0 or (attBombard > 0 and tCityOnTile ~= nil)) and dist <= attRange
local effAttCS = isRanged and (attRS > 0 and attRS or attBombard) or attCS
-- Find defender
local enemy = nil
if tCityOnTile == nil then
    local tgtUnits = Map.GetUnitsAt({target_x}, {target_y})
    if tgtUnits then
        for other in tgtUnits:Units() do
            if other:GetOwner() ~= me then
                local eInfo = GameInfo.Units[other:GetType()]
                local eCombat = eInfo and eInfo.Combat or 0
                if eCombat > 0 or enemy == nil then enemy = other end
                if eCombat > 0 then break end
            end
        end
    end
end
if enemy == nil then
    -- A city with no garrison in it is still a legal target. Map.GetUnitsAt sees no defender,
    -- so the estimate is synthesised for the city itself: defender CS 0 makes the narrator say
    -- what is true - the CITY takes the damage, and the damage formula does not apply to it.
    local tCity = nil
    pcall(function() tCity = Cities.GetCityInPlot({target_x}, {target_y}) end)
    if tCity == nil then {_bail(f"ERR:NO_ENEMY|No hostile unit or city at ({target_x},{target_y})")} end
    local cName = "unknown"
    pcall(function() cName = Locale.Lookup(tCity:GetName()):gsub("|", "/") end)
    local cHP, cMax = 0, 0
    pcall(function()
        local ccIdx = GameInfo.Districts["DISTRICT_CITY_CENTER"].Index
        for _, d in tCity:GetDistricts():Members() do
            if d:GetType() == ccIdx then
                cMax = d:GetMaxDamage(DefenseTypes.DISTRICT_GARRISON) or 0
                cHP = cMax - (d:GetDamage(DefenseTypes.DISTRICT_GARRISON) or 0)
                break
            end
        end
    end)
    -- `myHP` is defined further down this function (it reads the defender's pool first), so the
    -- attacker's HP is read here rather than concatenated as a nil - live T102, an ungarrisoned
    -- city answered "operator .. is not supported for nil .. string" instead of an estimate.
    local myHPNow = unit:GetMaxDamage() - unit:GetDamage()
    print("ESTIMATE|" .. attType .. "|CITY_CENTER|" .. effAttCS .. "|0|" .. (isRanged and "1" or "0")
        .. "||" .. myHPNow .. "|" .. cHP .. "|" .. cName .. "|")
    print("{SENTINEL}")
    return
end
-- Check diplomatic status —estimates for units at peace are misleading
local enemyOwner = enemy:GetOwner()
if enemyOwner ~= 63 then
    local pDiplo = Players[me]:GetDiplomacy()
    if not pDiplo:IsAtWarWith(enemyOwner) then
        local ownerCfg = PlayerConfigurations[enemyOwner]
        local ownerName = ownerCfg and Locale.Lookup(ownerCfg:GetCivilizationDescription()) or ("player " .. enemyOwner)
        local eInfo2 = GameInfo.Units[enemy:GetType()]
        local eName = eInfo2 and eInfo2.UnitType or "UNKNOWN"
        {_bail_lua('"ERR:NOT_AT_WAR|Cannot attack " .. eName .. " —you are at peace with " .. ownerName .. ". Declare war first."')}
    end
end
local eInfo = GameInfo.Units[enemy:GetType()]
local defType = eInfo and eInfo.UnitType or "UNKNOWN"
local defCS = eInfo and eInfo.Combat or 0
-- The defender's domain travels with the estimate: "melee versus a unit at sea" is not a weak
-- attack, it is not an attack (manual:723), and the estimate must be able to say so instead of
-- printing a damage number for a blow that cannot land.
local defDomain = eInfo and eInfo.Domain or ""
local enemyHP = enemy:GetMaxDamage() - enemy:GetDamage()
local myHP = unit:GetMaxDamage() - unit:GetDamage()
-- Build promotion -> CS bonus lookup table
local promoBonuses = {{}}
pcall(function()
    for pm in GameInfo.UnitPromotionModifiers() do
        local mod = GameInfo.Modifiers[pm.ModifierId]
        if mod and mod.ModifierType == "MODIFIER_UNIT_ADJUST_COMBAT_STRENGTH" then
            for arg in GameInfo.ModifierArguments() do
                if arg.ModifierId == pm.ModifierId and arg.Name == "Amount" then
                    local val = tonumber(arg.Value) or 0
                    if val ~= 0 then
                        if not promoBonuses[pm.UnitPromotionType] then
                            promoBonuses[pm.UnitPromotionType] = {{}}
                        end
                        table.insert(promoBonuses[pm.UnitPromotionType], {{
                            amount = val,
                            name = pm.ModifierId
                        }})
                    end
                end
            end
        end
    end
end)
-- Sum promotion bonuses for a unit
local function getPromoBonuses(u)
    local total = 0
    local parts = {{}}
    local exp = u:GetExperience()
    for promoType, infos in pairs(promoBonuses) do
        local promoRow = GameInfo.UnitPromotions[promoType]
        if promoRow then
            local ok, has = pcall(function() return exp:HasPromotion(promoRow.Index) end)
            if ok and has then
                for _, info in ipairs(infos) do
                    total = total + info.amount
                    local short = info.name:gsub("MODIFIER_", "")
                    table.insert(parts, short .. " " .. (info.amount > 0 and "+" or "") .. info.amount)
                end
            end
        end
    end
    return total, parts
end
-- Gather modifiers
local mods = {{}}
local defModTotal = 0
local attModTotal = 0
-- Attacker promotion bonuses
local attPromoBonus, attPromoMods = getPromoBonuses(unit)
if attPromoBonus ~= 0 then
    attModTotal = attModTotal + attPromoBonus
    for _, m in ipairs(attPromoMods) do table.insert(mods, "att " .. m) end
end
-- Defender promotion bonuses
local defPromoBonus, defPromoMods = getPromoBonuses(enemy)
if defPromoBonus ~= 0 then
    defModTotal = defModTotal + defPromoBonus
    for _, m in ipairs(defPromoMods) do table.insert(mods, "def " .. m) end
end
-- Defender fortified?
local ok1, ft = pcall(function() return enemy:GetFortifyTurns() end)
if ok1 and ft and ft > 0 then
    local bonus = math.min(ft * 3, 6)
    table.insert(mods, "fortified +" .. bonus)
    defModTotal = defModTotal + bonus
end
-- Defender on hills?
local tgtPlot = Map.GetPlot({target_x}, {target_y})
if tgtPlot and tgtPlot:IsHills() then
    table.insert(mods, "hills +3")
    defModTotal = defModTotal + 3
end
-- Forest/jungle defense bonus
if tgtPlot then
    local feat = tgtPlot:GetFeatureType()
    if feat >= 0 then
        local fInfo = GameInfo.Features[feat]
        if fInfo and (fInfo.FeatureType == "FEATURE_FOREST" or fInfo.FeatureType == "FEATURE_JUNGLE") then
            table.insert(mods, fInfo.FeatureType:gsub("FEATURE_",""):lower() .. " +3")
            defModTotal = defModTotal + 3
        end
    end
end
-- River crossing penalty (attacker crosses river for melee). The manual is explicit and this is
-- not a small number: "When attacking across a river, the attacking unit gets a -5 modifier to
-- its combat strength" (25th anniversary manual, RIVERS -> OFFENSIVE PENALTY; the same section
-- adds that crossing costs 3 movement points). This code used to say -2, which made every
-- across-the-river attack look two points better than the game would resolve it.
if not isRanged and tgtPlot then
    local attPlot = Map.GetPlot(ux, uy)
    if attPlot and tgtPlot:IsRiverCrossingToPlot(attPlot) then
        table.insert(mods, "river -5")
        attModTotal = attModTotal - 5
    end
end
-- Flanking: count our units adjacent to defender (excluding attacker)
local flankBonus = 0
if not isRanged then
    local enemyOwner = enemy:GetOwner()
    for dy = -1, 1 do for dx = -1, 1 do
        if dx ~= 0 or dy ~= 0 then
            local fx, fy = {target_x} + dx, {target_y} + dy
            -- The 3x3 box is not the hex neighbourhood: two of its eight plots sit two tiles
            -- away, and a unit standing there does not flank. Counting them made the estimate
            -- report "flank +6" for a pair the game's own preview calls "+4夹击加成" - measured
            -- live T113 against CombatManager.SimulateAttackVersus (UnitPanel.lua:3352), which
            -- is the engine's own answer to the same question.
            if Map.GetPlotDistance({target_x}, {target_y}, fx, fy) == 1
                and not (fx == ux and fy == uy) then
                local adjUnits = Map.GetUnitsAt(fx, fy)
                if adjUnits then
                    for adjU in adjUnits:Units() do
                        if adjU:GetOwner() == me then
                            local adjInfo = GameInfo.Units[adjU:GetType()]
                            if adjInfo and (adjInfo.Combat or 0) > 0 then
                                flankBonus = flankBonus + 2
                            end
                        end
                    end
                end
            end
        end
    end end
    if flankBonus > 0 then
        table.insert(mods, "flank +" .. flankBonus)
        attModTotal = attModTotal + flankBonus
    end
end
-- Support: count defender's adjacent friendlies (same hex-neighbourhood rule as flanking)
local supportBonus = 0
if not isRanged then
    local enemyOwner = enemy:GetOwner()
    for dy = -1, 1 do for dx = -1, 1 do
        if dx ~= 0 or dy ~= 0 then
            local sx, sy = {target_x} + dx, {target_y} + dy
            if Map.GetPlotDistance({target_x}, {target_y}, sx, sy) == 1 then
                local adjUnits = Map.GetUnitsAt(sx, sy)
                if adjUnits then
                    for adjU in adjUnits:Units() do
                        if adjU:GetOwner() == enemyOwner and adjU ~= enemy then
                            local adjInfo = GameInfo.Units[adjU:GetType()]
                            if adjInfo and (adjInfo.Combat or 0) > 0 then
                                supportBonus = supportBonus + 2
                            end
                        end
                    end
                end
            end
        end
    end end
    if supportBonus > 0 then
        table.insert(mods, "support +" .. supportBonus)
        defModTotal = defModTotal + supportBonus
    end
end
local effDefCS = defCS + defModTotal
effAttCS = effAttCS + attModTotal
-- A city on the target tile changes what an attack means. The defender found
-- above is whatever unit occupies the tile, but the thing that takes damage is
-- the CITY, and when that unit has 0 combat strength the formula below returns
-- a meaningless ~0 that reads as "this attack does nothing". Seen live on T167:
-- seven attacks reported "Est damage to defender: ~0" while the walls went
-- 13 -> 3. Cities.GetCityInPlot(x, y) is the API the game's own UI uses
-- (UnitFlagManager.lua:941, WorldInput.lua:456); pcall guards the probe so a
-- failure cannot break the estimate.
local tCity = nil
pcall(function() tCity = Cities.GetCityInPlot({target_x}, {target_y}) end)
local tCityName = ""
if tCity then tCityName = Locale.Lookup(tCity:GetName()):gsub("|", "/") end
print("ESTIMATE|" .. attType .. "|" .. defType .. "|" .. effAttCS .. "|" .. effDefCS .. "|" .. (isRanged and "1" or "0") .. "|" .. table.concat(mods, ";") .. "|" .. myHP .. "|" .. enemyHP .. "|" .. tCityName .. "|" .. defDomain)
print("{SENTINEL}")
"""


def parse_combat_estimate(
    lines: list[str], att_cs: int, def_cs: int
) -> CombatEstimate | None:
    """Parse ESTIMATE line and compute damage using Civ 6 formula."""
    for line in lines:
        if line.startswith("ESTIMATE|"):
            p = line.split("|")
            if len(p) < 9:
                return None
            eff_att = int(p[3])
            eff_def = int(p[4])
            is_ranged = p[5] == "1"
            mods = [m for m in p[6].split(";") if m]
            my_hp = int(p[7])
            enemy_hp = int(p[8])
            # Civ 6 damage formula: BASE * 10^((att-def)/30)

            base_damage = 24
            if eff_att > 0 and eff_def > 0:
                dmg_to_def = base_damage * (10 ** ((eff_att - eff_def) / 30))
                dmg_to_att = (
                    base_damage * (10 ** ((eff_def - eff_att) / 30))
                    if not is_ranged
                    else 0
                )
            else:
                dmg_to_def = 0
                dmg_to_att = 0
            return CombatEstimate(
                attacker_type=p[1],
                defender_type=p[2],
                attacker_cs=eff_att,
                defender_cs=eff_def,
                is_ranged=is_ranged,
                modifiers=mods,
                est_damage_to_defender=int(round(dmg_to_def)),
                est_damage_to_attacker=int(round(dmg_to_att)),
                defender_hp=enemy_hp,
                attacker_hp=my_hp,
                target_city=p[9] if len(p) > 9 else "",
                defender_domain=p[10] if len(p) > 10 else "",
            )
    return None


def build_threat_scan_query() -> str:
    """GameCore: scan for foreign military units visible to the player.

    Scans all players (not just barbarians) but only reports units on tiles
    the player can currently see (PlayersVisibility:IsVisible). No arbitrary
    distance limits —fog of war is the natural filter.

    Uses GameCore context but filters by fog of war —only reports units
    on tiles the player can currently see (PlayersVisibility:IsVisible).
    Reports owner, HP, combat strength, and distance from nearest friendly position.
    """
    return """
local me = Game.GetLocalPlayer()
local pDiplo = Players[me]:GetDiplomacy()
local pVis = PlayersVisibility[me]
local myPos = {}
local unitPos = {}
local milPos = {}
for _, c in Players[me]:GetCities():Members() do
    table.insert(myPos, {c:GetX(), c:GetY()})
end
for _, u in Players[me]:GetUnits():Members() do
    local ux, uy = u:GetX(), u:GetY()
    if ux ~= -9999 then
        table.insert(myPos, {ux, uy})
        table.insert(unitPos, {ux, uy})
        local uEntry = GameInfo.Units[u:GetType()]
        local ucs = uEntry and uEntry.Combat or 0
        local urs = uEntry and uEntry.RangedCombat or 0
        if ucs > 0 or urs > 0 then table.insert(milPos, {ux, uy}) end
    end
end
local found = false
for pid = 0, 63 do
    if pid ~= me and Players[pid] and Players[pid]:IsAlive() then
        local isMajor = Players[pid]:IsMajor()
        local isBarbarian = (pid == 63)
        -- Skip city-state units unless we're at war with them
        if not isMajor and not isBarbarian and not pDiplo:IsAtWarWith(pid) then
            -- City-state, not at war —not a threat
        else
        local ownerName = "Barbarian"
        if pid ~= 63 then
            local cfg = PlayerConfigurations[pid]
            if cfg then ownerName = Locale.Lookup(cfg:GetCivilizationShortDescription()) end
        end
        for _, bu in Players[pid]:GetUnits():Members() do
            local bx, by = bu:GetX(), bu:GetY()
            if bx ~= -9999 and pVis:IsVisible(bx, by) then
                local uType = bu:GetType()
                if uType then
                    local entry = GameInfo.Units[uType]
                    local bcs = entry and entry.Combat or 0
                    local minDist = 999
                    for _, pos in ipairs(myPos) do
                        local d = Map.GetPlotDistance(pos[1], pos[2], bx, by)
                        if d < minDist then minDist = d end
                    end
                    -- Distance to the nearest of our *units*, ignoring cities: "the enemy
                    -- is next to the army" is a different fact from "next to our borders",
                    -- and the first one is what the march rule needs.
                    local minUnit = 999
                    for _, pos in ipairs(unitPos) do
                        local d = Map.GetPlotDistance(pos[1], pos[2], bx, by)
                        if d < minUnit then minUnit = d end
                    end
                    -- **Religious units are civilians with `ReligiousStrength`** (Missionary 100,
                    -- Apostle 350, Inquisitor 200, Guru 200 - `Base/Assets/Gameplay/Data/Units.xml`).
                    -- There is no `FORMATION_CLASS_RELIGIOUS` in the game's data: a Missionary is
                    -- `FORMATION_CLASS_CIVILIAN` with no `PromotionClass` at all, which is why the
                    -- combat filter below never matched one and no metric ever saw a missionary.
                    -- The at-war flag is reported rather than filtered: at peace the doctrine is to
                    -- leave the unit alone (never declare war over missionaries alone), and the
                    -- caller has to be able to tell the two cases apart.
                    local rstr = (entry and entry.ReligiousStrength) or 0
                    if rstr > 0 then
                        local atWarWith = false
                        if pid ~= 63 then
                            pcall(function() atWarWith = pDiplo:IsAtWarWith(pid) end)
                        end
                        print("RELIGIOUS|" .. pid .. "|" .. ownerName:gsub("|","/") .. "|"
                            .. (entry and entry.UnitType or "UNKNOWN") .. "|" .. bx .. "," .. by
                            .. "|" .. (bu:GetMaxDamage() - bu:GetDamage()) .. "/" .. bu:GetMaxDamage()
                            .. "|rstr:" .. rstr .. "|dist:" .. minDist .. "|udist:" .. minUnit
                            .. "|atwar:" .. (atWarWith and 1 or 0)
                            .. "|uid:" .. bu:GetID())
                    end
                    if bcs > 0 or (entry and entry.RangedCombat and entry.RangedCombat > 0) then
                        -- How many of our fighting units are close enough to join this one:
                        -- one is a trade, two or three is a kill.
                        local near = 0
                        local adj = 0
                        for _, pos in ipairs(milPos) do
                            local d = Map.GetPlotDistance(pos[1], pos[2], bx, by)
                            if d <= 2 then near = near + 1 end
                            if d <= 1 then adj = adj + 1 end
                        end
                        local name = entry and entry.UnitType or "UNKNOWN"
                        local hp = bu:GetMaxDamage() - bu:GetDamage()
                        local brs = entry and entry.RangedCombat or 0
                        local isCS = Players[pid]:IsMajor() and "0" or "1"
                        -- PromotionClass is the game's own counter axis (MELEE, RANGED, LIGHT_CAVALRY,
                        -- HEAVY_CAVALRY, ANTI_CAVALRY, SIEGE, RECON, NAVAL_*), so the caller can ask
                        -- "is there cavalry next to the army" without a hardcoded unit-name table.
                        local pc = ""
                        pcall(function() pc = entry and entry.PromotionClass or "" end)
                        print("THREAT|" .. pid .. "|" .. ownerName:gsub("|","/") .. "|" .. name .. "|" .. bx .. "," .. by .. "|" .. hp .. "/" .. bu:GetMaxDamage() .. "|CS:" .. bcs .. "|RS:" .. brs .. "|dist:" .. minDist .. "|cs:" .. isCS .. "|uid:" .. bu:GetID() .. "|pc:" .. pc .. "|udist:" .. minUnit .. "|near:" .. near .. "|adj:" .. adj)
                        found = true
                    end
                end
            end
        end
        end -- close city-state skip if/else
    end -- close if pid alive
end -- close for pid
if not found then print("NO_THREATS") end
print("{SENTINEL}")
""".replace("{SENTINEL}", SENTINEL)


def build_pillage_unit(unit_index: int, target_x: int | None = None, target_y: int | None = None) -> str:
    """InGame: pillage the improvement or district on the unit's tile (or a named tile).

    The verb the directive has been ordering since the first draft - "pillaging that Holy Site ...
    is worth more than any number of individual kills" - and the one standing order the toolkit could
    not carry out: `unit_action` had no `pillage` case and no pillage code existed anywhere in
    `src/`. The staging ladder even offered it as a rung.

    The game's own operation is `UNITOPERATION_PILLAGE` (`Base/Assets/Gameplay/Data/UnitOperations.xml`),
    so this asks `UnitManager.CanStartOperation` first - the same authoritative test `attack` and
    `move` use - and reports *what* is on the tile before it acts, because "nothing to pillage here"
    and "the improvement is already pillaged" are different answers and the second one is the common
    mistake after a repair.
    """
    tx = -9999 if target_x is None else int(target_x)
    ty = -9999 if target_y is None else int(target_y)
    return f"""
{_lua_get_unit(unit_index)}
local ux, uy = unit:GetX(), unit:GetY()
if unit:GetMovesRemaining() <= 0 then
    {_bail("ERR:NO_MOVES|Unit has no movement points remaining this turn.")}
end
local tx, ty = {tx}, {ty}
if tx == -9999 then tx, ty = ux, uy end
local plot = Map.GetPlot(tx, ty)
if not plot then
    {_bail_lua('"ERR:INVALID_TARGET|No plot at (" .. tx .. "," .. ty .. ")"')}
end
local dist = Map.GetPlotDistance(ux, uy, tx, ty)
if dist > 1 then
    {_bail_lua('"ERR:OUT_OF_RANGE|Target at distance " .. dist .. " - a unit pillages the tile it stands on (or one it is adjacent to at most)."')}
end
-- What is here, before asking the engine: an improvement, a district, a route.
local imp, impPillaged, dist2, distPillaged, route = "none", false, "none", false, -1
pcall(function()
    local ii = plot:GetImprovementType()
    if ii >= 0 then
        local iInfo = GameInfo.Improvements[ii]
        if iInfo then imp = iInfo.ImprovementType end
        impPillaged = plot:IsImprovementPillaged()
    end
end)
pcall(function()
    local di = plot:GetDistrictType()
    if di >= 0 then
        local dInfo = GameInfo.Districts[di]
        if dInfo then dist2 = dInfo.DistrictType end
    end
end)
pcall(function() route = plot:GetRouteType() end)
print("PILLAGE_TILE|" .. tx .. "," .. ty .. "|improvement:" .. imp
    .. "|pillaged:" .. (impPillaged and 1 or 0) .. "|district:" .. dist2
    .. "|route:" .. route .. "|owner:" .. plot:GetOwner())
if imp == "none" and dist2 == "none" and route < 0 then
    {_bail_lua('"ERR:NOTHING_TO_PILLAGE|Nothing to pillage at (" .. tx .. "," .. ty .. "): no improvement, no district and no road."')}
end
local params = {{}}
params[UnitOperationTypes.PARAM_X] = {{tx}}
params[UnitOperationTypes.PARAM_Y] = {{ty}}
local ok, can = pcall(function()
    return UnitManager.CanStartOperation(unit, UnitOperationTypes.PILLAGE, nil, params)
end)
if not ok or not can then
    local why = "the engine refused the order"
    if impPillaged then why = "the improvement here is **already pillaged**" end
    {_bail_lua('"ERR:CANNOT_PILLAGE|Cannot pillage (" .. tx .. "," .. ty .. ") - " .. why .. ". Re-read the tile with get_map_area; a pillaged improvement pays nothing until it is repaired."')}
end
UnitManager.RequestOperation(unit, UnitOperationTypes.PILLAGE, params)
print("OK:PILLAGE|" .. (imp ~= "none" and imp or (dist2 ~= "none" and dist2 or "route"))
    .. " at (" .. tx .. "," .. ty .. ")|plunder arrives with the next read|verify with get_map_area (the tile reports PILLAGED) or get_cities (pillaged improvements)")
print("{SENTINEL}")
"""


def build_fortify_unit(unit_index: int) -> str:
    return f"""
{_lua_get_unit(unit_index)}
if unit:GetFortifyTurns() > 0 then
    print("OK:ALREADY_FORTIFIED|Fortify turns: " .. unit:GetFortifyTurns())
    print("{SENTINEL}"); return
end
if UnitManager.CanStartOperation(unit, UnitOperationTypes.FORTIFY, nil, true) then
    UnitManager.RequestOperation(unit, UnitOperationTypes.FORTIFY)
    print("OK:FORTIFIED")
else
    local sleepOp = GameInfo.UnitOperations["UNITOPERATION_SLEEP"]
    if sleepOp and UnitManager.CanStartOperation(unit, sleepOp.Hash, nil, true) then
        UnitManager.RequestOperation(unit, sleepOp.Hash)
        print("OK:SLEEPING")
    else
        {_bail("ERR:CANNOT_FORTIFY|Unit cannot fortify or sleep")}
    end
end
print("{SENTINEL}")
"""


def build_condemn_heretic(unit_index: int) -> str:
    """Condemn Heretic: destroy an adjacent enemy religious unit.

    The game exposes this as a **command**, not a UnitOperation —    `UNITCOMMAND_CONDEMN_HERETIC` in the install's
    `Base/Assets/Gameplay/Data/UnitCommands.xml`, issued with
    `UnitManager.RequestCommand(unit, UnitCommandTypes.CONDEMN_HERETIC)` and pre-checked with
    `UnitManager.CanStartCommand(...)` (the same pair the game's own UnitPanel uses). There is no
    target parameter: the engine picks the adjacent religious unit, so this reports every
    candidate before it fires rather than condemning one silently.

    **The game itself requires a war declaration** for this —its own refusal string is
    `LOC_UNITCOMMAND_CONDEMN_HERETIC_REQUIRES_WAR_DECLARATION`: "A Religious unit in this tile
    belongs to a player you are not at war with." So a missionary of a civ we are at peace with
    cannot be condemned by anyone, tool or human; the case this exists for is a religious unit of
    the civ we are at war with.

    Religious units are civilians by formation class (the Missionary is `CLASS_LANDCIVILIAN` with
    the `CLASS_RELIGIOUS` tag), so the target test is on the unit type, not the formation class.
    """
    return f"""
{_lua_get_unit(unit_index)}
local ux, uy = unit:GetX(), unit:GetY()
local RELIGIOUS = {{ UNIT_MISSIONARY = true, UNIT_APOSTLE = true, UNIT_INQUISITOR = true, UNIT_GURU = true }}
local found = {{}}
for dx = -2, 2 do
  for dy = -2, 2 do
    local px, py = ux + dx, uy + dy
    if Map.GetPlotDistance(ux, uy, px, py) == 1 then
      local plotUnits = Map.GetUnitsAt(px, py)
      if plotUnits then
        for other in plotUnits:Units() do
          if other:GetOwner() ~= me then
            local oInfo = GameInfo.Units[other:GetType()]
            if oInfo and RELIGIOUS[oInfo.UnitType] then
              local oName, oOwner = oInfo.UnitType, tostring(other:GetOwner())
              pcall(function() oName = Locale.Lookup(oInfo.Name) end)
              pcall(function() oOwner = Locale.Lookup(PlayerConfigurations[other:GetOwner()]:GetCivilizationShortDescription()) end)
              table.insert(found, {{ other, px, py, oName, oOwner }})
            end
          end
        end
      end
    end
  end
end
if #found == 0 then
  {_bail("ERR:NO_RELIGIOUS_TARGET|No adjacent enemy religious unit to condemn (no Missionary, Apostle, Inquisitor or Guru within one tile)")}
end
for _, f in ipairs(found) do
  print("CANDIDATE|" .. f[4] .. "|" .. f[5] .. "|at (" .. f[2] .. "," .. f[3] .. ")")
end
local target, tx, ty, tName, tOwner = found[1][1], found[1][2], found[1][3], found[1][4], found[1][5]
local command = UnitCommandTypes.CONDEMN_HERETIC
if not command then
  {_bail("ERR:NO_CONDEMN_COMMAND|This game build does not expose UnitCommandTypes.CONDEMN_HERETIC")}
end
local canStart = false
local okCan, canStartResult = pcall(function() return UnitManager.CanStartCommand(unit, command, nil, true) end)
if okCan and canStartResult then canStart = true end
if not canStart then
  local atWar = false
  pcall(function() atWar = Players[me]:GetDiplomacy():IsAtWarWith(target:GetOwner()) end)
  print("TARGET|" .. tName .. "|" .. tOwner .. "|at (" .. tx .. "," .. ty .. ")")
  if not atWar then
    {_bail("ERR:REQUIRES_WAR|Condemn Heretic needs a war declaration - the game refuses it against a player we are not at war with (LOC_UNITCOMMAND_CONDEMN_HERETIC_REQUIRES_WAR_DECLARATION). Declare war first; task 007 owns that decision.")}
  end
  {_bail("ERR:CANNOT_CONDEMN|The game will not start Condemn Heretic for this unit right now (no charges left, already acted, or no legal adjacent target).")}
end
UnitManager.RequestCommand(unit, command)
print("OK:CONDEMNED|" .. tName .. " of " .. tOwner .. " at (" .. tx .. "," .. ty .. ")|candidates:" .. #found .. "|verify_tile:" .. tx .. "," .. ty)
print("{SENTINEL}")
"""


def build_skip_unit(unit_index: int) -> str:
    """Skip a unit's turn (GameCore context —uses FinishMoves)."""
    return f"""
{_lua_get_unit_gamecore(unit_index)}
UnitManager.FinishMoves(unit)
print("OK:SKIPPED")
print("{SENTINEL}")
"""


def build_fortify_remaining_units() -> str:
    """Fortify/heal combat units with remaining moves (InGame context).

    Tries to fortify (or heal if damaged) combat units. Non-combat units
    and units that can't fortify are left for skip_remaining_units to handle.
    """
    return """
local me = Game.GetLocalPlayer()
local fortified = 0
local healed = 0
local healHash = GameInfo.UnitOperations["UNITOPERATION_HEAL"] and GameInfo.UnitOperations["UNITOPERATION_HEAL"].Hash
for _, unit in Players[me]:GetUnits():Members() do
    local x = unit:GetX()
    if x ~= -9999 and unit:GetMovesRemaining() > 0 then
        local info = GameInfo.Units[unit:GetType()]
        local isCombat = info and info.Combat > 0
        if isCombat then
            if unit:GetDamage() > 0 and healHash then
                local ok = pcall(function()
                    if UnitManager.CanStartOperation(unit, healHash, nil, true) then
                        UnitManager.RequestOperation(unit, healHash)
                        healed = healed + 1
                    end
                end)
            else
                local ok = pcall(function()
                    if UnitManager.CanStartOperation(unit, UnitOperationTypes.FORTIFY, nil, true) then
                        UnitManager.RequestOperation(unit, UnitOperationTypes.FORTIFY)
                        fortified = fortified + 1
                    end
                end)
            end
        end
    end
end
print("OK:FORTIFIED|" .. fortified .. " fortified, " .. healed .. " healing")
print("{SENTINEL}")
""".replace("{SENTINEL}", SENTINEL)


def build_unused_attack_query() -> str:
    """GameCore: our units that still have moves *and* a legal attack they have not used.

    `get_units` advertises the same thing per unit as a `>> CAN ATTACK` line, but that line
    is only in front of the agent on the turns it happens to call `get_units`, and it is one
    line among fifteen. This query exists so the omission can be reported where it happens:
    the turn result, and just before `skip_remaining_units` closes the turn by finishing the
    moves of units that never attacked.

    The legality test mirrors the units query exactly (adjacency for melee, LOS through
    `CanStartOperation` for ranged beyond one tile, barbarians always hostile, war required
    otherwise), so this report can never contradict the `CAN ATTACK` hints.

    Three things that are *not* attacks are excluded, because a report that cries wolf gets
    ignored - measured T213-T215, `skip_remaining_units(force=True)` was discarding three
    phantom entries per turn while `use-your-attacks` failed on them:

    * a **siege unit** cannot attack units at all (`ERR:SIEGE_CANNOT_ATTACK_UNITS`), so it is
      not scanned against unit targets;
    * a unit with **no attacks left** (`GetAttacksRemaining`, the same test the game's own
      SelectedUnit.lua uses) is not holding an attack;
    * a unit that **entered a Zone of Control this turn** cannot attack until next turn
      (`HasMovedIntoZOC`, the check `unit_action` already enforces).

    If the game's attack-count API is missing, the unit is reported rather than silently
    dropped: a false alarm is cheaper than a lost attack.
    """
    return """
local me = Game.GetLocalPlayer()
local out = {}
local function attacks_left(u)
    local ok, n = pcall(function() return u:GetAttacksRemaining() end)
    if ok and n ~= nil then return n end
    return 1
end
for _, unit in Players[me]:GetUnits():Members() do
    local x = unit:GetX()
    local y = unit:GetY()
    if x ~= -9999 and unit:GetMovesRemaining() > 0 then
        local entry = GameInfo.Units[unit:GetType()]
        local cs = entry and entry.Combat or 0
        local rs = entry and entry.RangedCombat or 0
        -- Siege units carry their ranged strength in `Bombard`, not `RangedCombat`
        -- (UNIT_CATAPULT is Combat 25 / RangedCombat 0 / Bombard 35 / Range 2), so a test that
        -- only looks at RangedCombat declares a Catapult a range-1 melee unit and reports no
        -- legal targets at the two tiles it actually bombards. Measured live 2026-09-25: a
        -- Catapult standing at distance 2 from Moscow came back with an empty target list.
        local bomb = entry and entry.Bombard or 0
        local shoots = (rs > 0) or (bomb > 0)
        -- ...but the same Bombard value means it cannot touch a *unit*: only RangedCombat
        -- units may. Its unused shot at a city is SIEGE FIRE's business, not this scan's.
        local can_hit_units = (rs > 0) or not shoots
        -- **A melee land unit cannot attack a unit at sea** (manual:723). The action path refuses it
        -- by name (`ERR:MELEE_CANNOT_ATTACK_AT_SEA`, the same `Domain` test), so counting it here
        -- makes the end-turn guard refuse a turn over an attack that can never be made - and the
        -- only exit is `--force`, which discards the real unused attacks with it. Measured live
        -- T95-T97: `UNIT_HEAVY_CHARIOT@60,14 -> UNIT_GALLEY@59,13` and the Warrior beside it were
        -- listed every single turn against a Barbarian Galley sitting in our own harbour, and both
        -- came back `MELEE_CANNOT_ATTACK_AT_SEA` when ordered.
        local landMelee = (not shoots) and entry ~= nil and entry.Domain == "DOMAIN_LAND"
        if (cs > 0 or shoots) and can_hit_units
            and attacks_left(unit) > 0 and not unit:HasMovedIntoZOC() then
            local rng = shoots and (entry and entry.Range or 1) or 1
            local hits = {}
            for dy = -rng, rng do
                for dx = -rng, rng do
                    local tx, ty = x + dx, y + dy
                    local d = Map.GetPlotDistance(x, y, tx, ty)
                    if d >= 1 and d <= rng then
                        local plotUnits = Map.GetUnitsAt(tx, ty)
                        if plotUnits then
                            for other in plotUnits:Units() do
                                local otherOwner = other:GetOwner()
                                if otherOwner ~= me and (otherOwner == 63 or Players[me]:GetDiplomacy():IsAtWarWith(otherOwner)) then
                                    local losOK = true
                                    -- Ask the engine at every distance, not only beyond one tile:
                                    -- a range-1 shooter (Crouching Tiger) can be refused too.
                                    if shoots then
                                        local lp = {}
                                        lp[UnitOperationTypes.PARAM_X] = tx
                                        lp[UnitOperationTypes.PARAM_Y] = ty
                                        losOK = UnitManager.CanStartOperation(unit, UnitOperationTypes.RANGE_ATTACK, nil, lp)
                                    end
                                    if losOK then
                                        local eInfo = GameInfo.Units[other:GetType()]
                                        local eHP = other:GetMaxDamage() - other:GetDamage()
                                        local atSea = eInfo ~= nil and eInfo.Domain == "DOMAIN_SEA"
                                        if not (landMelee and atSea) then
                                            table.insert(hits, (eInfo and eInfo.UnitType or "UNKNOWN") .. "@" .. tx .. "," .. ty .. "(" .. eHP .. "hp)")
                                        end
                                    end
                                end
                            end
                        end
                    end
                end
            end
            if #hits > 0 then
                table.insert(out, (entry and entry.UnitType or "?") .. "|" .. unit:GetID() .. "|" .. x .. "," .. y .. "|" .. table.concat(hits, ";"))
            end
        end
    end
end
if #out == 0 then print("NO_UNUSED_ATTACKS") end
for _, line in ipairs(out) do print("UNUSED_ATTACK|" .. line) end
print("{SENTINEL}")
""".replace("{SENTINEL}", SENTINEL)


def parse_unused_attack_response(lines: list[str]) -> list[str]:
    """One readable entry per unit that left a legal attack unused.

    ``UNUSED_ATTACK|UNIT_HEAVY_CHARIOT|1310724|53,36|UNIT_SWORDSMAN@53,35(7hp)`` becomes
    ``UNIT_HEAVY_CHARIOT@53,36 -> UNIT_SWORDSMAN@53,35(7hp)``.
    """
    entries: list[str] = []
    for line in lines:
        if not line.startswith("UNUSED_ATTACK|"):
            continue
        parts = line.split("|")
        if len(parts) < 5:
            continue
        unit_type, _uid, where, targets = parts[1], parts[2], parts[3], parts[4]
        entries.append(f"{unit_type}@{where} -> {targets}")
    return entries


def build_siege_posture_query() -> str:
    """GameCore: where our siege units stand, and whether anything is in front of them.

    Before an assault the army stages **outside** the enemy's reach (a city's ranged strike
    reaches two tiles), the units that can take a hit stand in front, and the ranged and siege
    units stand behind - with the siege unit's tile treated as the one that must be protected,
    because a Catapult is the most expensive and most fragile thing in the stack. This asks the
    game for exactly that geometry: for each of our siege units, the distance to the nearest
    visible enemy unit, the distance from that enemy to the front-line unit closest to the siege
    unit (the screen), and the distance to the nearest visible enemy city.

    The game does all the distance work with ``Map.GetPlotDistance``, so no hex arithmetic is
    guessed on the Python side.
    """
    return """
local me = Game.GetLocalPlayer()
local pVis = PlayersVisibility[me]
local pDiplo = Players[me]:GetDiplomacy()
local screens = {}
local siege = {}
for _, u in Players[me]:GetUnits():Members() do
    local ux, uy = u:GetX(), u:GetY()
    if ux ~= -9999 then
        local entry = GameInfo.Units[u:GetType()]
        local pc = ""
        pcall(function() pc = entry and entry.PromotionClass or "" end)
        local cs = entry and entry.Combat or 0
        local rs = entry and entry.RangedCombat or 0
        if cs > 0 or rs > 0 then
            local uType = entry and entry.UnitType or "?"
            if string.find(pc, "SIEGE") then
                table.insert(siege, {uType, ux, uy, entry and entry.Range or 1})
            elseif string.find(pc, "MELEE") or string.find(pc, "CAVALRY") then
                table.insert(screens, {ux, uy})
            end
        end
    end
end
if #siege == 0 then
    print("NO_SIEGE")
    print("{SENTINEL}")
    return
end
local enemies = {}
local cities = {}
for pid = 0, 63 do
    if pid ~= me and Players[pid] and Players[pid]:IsAlive() then
        local isBarb = (pid == 63)
        if isBarb or Players[pid]:IsMajor() or pDiplo:IsAtWarWith(pid) then
            for _, bu in Players[pid]:GetUnits():Members() do
                local bx, by = bu:GetX(), bu:GetY()
                if bx ~= -9999 and pVis:IsVisible(bx, by) then
                    local be = GameInfo.Units[bu:GetType()]
                    local bcs = be and be.Combat or 0
                    local brs = be and be.RangedCombat or 0
                    if bcs > 0 or brs > 0 then table.insert(enemies, {bx, by}) end
                end
            end
            pcall(function()
                for _, c in Players[pid]:GetCities():Members() do
                    local cx, cy = c:GetX(), c:GetY()
                    if pVis:IsVisible(cx, cy) then
                        -- The fourth field is whether we are at war with the city's owner. Every
                        -- visible major city is reported (the staging state - a gun three or four
                        -- tiles from the *future* target - is what `tactics/04` plans the rally for,
                        -- and it exists before any declaration), but a rule that counts guns "in
                        -- range of a city" must be able to tell an enemy's walls from a friend's.
                        table.insert(cities, {cx, cy, Locale.Lookup(c:GetName()),
                            pDiplo:IsAtWarWith(pid) and true or false})
                    end
                end
            end)
        end
    end
end
for _, s in ipairs(siege) do
    local eDist = 999
    for _, e in ipairs(enemies) do
        local d = Map.GetPlotDistance(s[2], s[3], e[1], e[2])
        if d < eDist then eDist = d end
    end
    local scrDist = 999
    local scrEnemyDist = 999
    for _, sc in ipairs(screens) do
        local d = Map.GetPlotDistance(sc[1], sc[2], s[2], s[3])
        if d < scrDist then
            scrDist = d
            scrEnemyDist = 999
            for _, e in ipairs(enemies) do
                local de = Map.GetPlotDistance(sc[1], sc[2], e[1], e[2])
                if de < scrEnemyDist then scrEnemyDist = de end
            end
        end
    end
    local cDist, cName = 999, ""
    local wDist, wName = 999, ""
    for _, c in ipairs(cities) do
        local d = Map.GetPlotDistance(s[2], s[3], c[1], c[2])
        if d < cDist then cDist = d; cName = c[3] end
        -- `warcity` is the city we are actually besieging: the nearest one whose owner we are at
        -- war with, 999 when there is none. `city` stays the nearest city of any kind, because the
        -- *assembly* is judged against the city it is forming up to attack, before the declaration.
        if c[4] and d < wDist then wDist = d; wName = c[3] end
    end
    print("SIEGE_POSTURE|" .. s[1] .. "|" .. s[2] .. "," .. s[3] .. "|enemy:" .. eDist
        .. "|screen:" .. scrDist .. "|screen_enemy:" .. scrEnemyDist
        .. "|city:" .. cDist .. "|" .. cName:gsub("|", "/")
        .. "|warcity:" .. wDist .. "|" .. wName:gsub("|", "/")
        -- The gun's own range, appended last so an older parser reads the fields it knows and
        -- ignores this one. `city_distance` is measured to the city; whether the gun can *fire*
        -- from there is this number against that one (human instruction 2026-10-08).
        .. "|range:" .. (s[4] or 2))
end
print("{SENTINEL}")
""".replace("{SENTINEL}", SENTINEL)


def parse_siege_posture_response(lines: list[str]) -> list[SiegePosture]:
    """``SIEGE_POSTURE|<type>|<x>,<y>|enemy:N|screen:N|screen_enemy:N|city:N|<name>|warcity:N|<name>``.

    ``city`` is the nearest visible city of **any** major civilisation - the reference the assembly
    is judged against, which exists before a declaration - and ``warcity`` (added 2026-10-02) is the
    nearest city of a civilisation **we are at war with**, which is the only one a siege rule may
    count. A server that predates the field sends eight tokens and ``warcity`` reads 999, "no enemy
    city in sight", never "the friend's city next door". ``range`` (added 2026-10-08) is the gun's
    own attack range, appended after ``warcity`` so the older fields keep their positions; it is
    what decides whether ``city_distance`` is a firing position or a walk.
    """
    postures: list[SiegePosture] = []
    for line in lines:
        if not line.startswith("SIEGE_POSTURE|"):
            continue
        parts = line.split("|")
        if len(parts) < 8:
            continue
        try:
            x_str, y_str = parts[2].split(",")
        except ValueError:
            continue

        def number(token: str) -> int:
            try:
                return int(token.split(":", 1)[1])
            except (IndexError, ValueError):
                return 999

        war_city_distance = 999
        war_city_name = ""
        if len(parts) >= 10 and parts[8].startswith("warcity:"):
            war_city_distance = number(parts[8])
            war_city_name = parts[9]
        # The gun's own range, appended by the current server. An older one does not send it and the
        # floor - 2 - is the reading, never 999.
        unit_range = 2
        if len(parts) >= 11 and parts[10].startswith("range:"):
            unit_range = number(parts[10])
            if unit_range < 1 or unit_range > 9:
                unit_range = 2

        postures.append(
            SiegePosture(
                unit_type=parts[1],
                x=int(x_str),
                y=int(y_str),
                enemy_distance=number(parts[3]),
                screen_distance=number(parts[4]),
                screen_enemy_distance=number(parts[5]),
                city_distance=number(parts[6]),
                city_name=parts[7],
                war_city_distance=war_city_distance,
                war_city_name=war_city_name,
                range=unit_range,
            )
        )
    return postures


def build_capture_check_query() -> str:
    """InGame: enemy cities in sight, and whether one of our melee units can take them.

    InGame rather than GameCore because an enemy city's districts and their damage pools are an
    InGame-only API (the same reason `build_attack_followup_query` runs there). Read-only.

    An assault has a last step that no damage number shows: a capture-capable unit walks onto the
    city's own tile once its HP pool is empty. Melee, anti-cavalry **and cavalry** can do it -
    live T122 a Heavy Chariot took Moscow this way; ranged, siege and support cannot (`CAPTURE_MOVE`
    from a Battering Ram is refused), and neither can a unit standing a tile away. This asks the
    game for exactly that, per visible enemy city: the city HP pool, the walls, and how many of our
    capture-capable units are adjacent or one tile out. Live, Moscow sat at 0/200 for four turns
    with a Spearman two tiles away, healed about twenty points a turn back to 120/200, and the
    siege had to be fought again from nothing.
    """
    return """
local me = Game.GetLocalPlayer()
local pVis = PlayersVisibility[me]
local pDiplo = Players[me]:GetDiplomacy()
local melee = {}
for _, u in Players[me]:GetUnits():Members() do
    local ux, uy = u:GetX(), u:GetY()
    if ux ~= -9999 then
        local entry = GameInfo.Units[u:GetType()]
        local pc = ""
        pcall(function() pc = entry and entry.PromotionClass or "" end)
        -- MELEE covers land melee and naval melee; ANTI_CAVALRY and CAVALRY can take cities too.
        -- SIEGE, RANGED and SUPPORT cannot. Cavalry used to be excluded here, and live T122 that
        -- was wrong: a Heavy Chariot walked into the Free City of Moscow at 0/200 and took it
        -- (our city count went 6 -> 7) while this scan reported `melee_adjacent 0`. The scan
        -- therefore stayed silent next to a city a chariot could walk into - the same class of
        -- miss the TAKE THE CITY block exists to prevent.
        if string.find(pc, "MELEE") or string.find(pc, "ANTI_CAVALRY")
            or string.find(pc, "CAVALRY") then
            table.insert(melee, {ux, uy, (entry and entry.UnitType or "?")})
        end
    end
end
for pid = 0, 63 do
    if pid ~= me and Players[pid] and Players[pid]:IsAlive() then
        local atWar = (pid == 63)
        if not atWar then pcall(function() atWar = pDiplo:IsAtWarWith(pid) end) end
        if atWar then
            pcall(function()
                for _, c in Players[pid]:GetCities():Members() do
                    local cx, cy = c:GetX(), c:GetY()
                    if pVis:IsVisible(cx, cy) then
                        local cHP, cMax, wHP, wMax = 0, 0, 0, 0
                        local ccIdx = GameInfo.Districts["DISTRICT_CITY_CENTER"].Index
                        for _, d in c:GetDistricts():Members() do
                            if d:GetType() == ccIdx then
                                wMax = d:GetMaxDamage(DefenseTypes.DISTRICT_OUTER) or 0
                                wHP = wMax - (d:GetDamage(DefenseTypes.DISTRICT_OUTER) or 0)
                                cMax = d:GetMaxDamage(DefenseTypes.DISTRICT_GARRISON) or 0
                                cHP = cMax - (d:GetDamage(DefenseTypes.DISTRICT_GARRISON) or 0)
                                break
                            end
                        end
                        local adj, near, who = 0, 0, ""
                        for _, m in ipairs(melee) do
                            local d = Map.GetPlotDistance(m[1], m[2], cx, cy)
                            if d <= 1 then
                                adj = adj + 1
                                who = m[3]
                            end
                            if d <= 2 then
                                near = near + 1
                                if who == "" then who = m[3] end
                            end
                        end
                        local cName = "unknown"
                        pcall(function() cName = Locale.Lookup(c:GetName()):gsub("|", "/") end)
                        -- Supply line, and whether it is still open. The manual (HEALING DAMAGE
                        -- TO CITIES) is explicit: "A city heals a small amount every turn, even
                        -- during combat, as long as it has a supply line. A supply line is any hex
                        -- adjacent to the city that is not within an enemy unit's Zone of
                        -- Control." So each adjacent hex is either cut - one of our military
                        -- units stands on it or beside it - or open, and a city with *every*
                        -- adjacent hex cut does not heal at all. That is a lever the army can
                        -- pull; out-damaging the healing is only the fallback.
                        local covered, total = 0, 0
                        local openHexes = {}
                        for sdx = -1, 1 do for sdy = -1, 1 do
                            if sdx ~= 0 or sdy ~= 0 then
                                local nx, ny = cx + sdx, cy + sdy
                                if Map.GetPlot(nx, ny)
                                    and Map.GetPlotDistance(cx, cy, nx, ny) == 1 then
                                    total = total + 1
                                    local cut = false
                                    local onHex = Map.GetUnitsAt(nx, ny)
                                    if onHex then
                                        for u2 in onHex:Units() do
                                            if u2:GetOwner() == me then
                                                local i2 = GameInfo.Units[u2:GetType()]
                                                if i2 and ((i2.Combat or 0) + (i2.RangedCombat or 0)) > 0 then
                                                    cut = true
                                                end
                                            end
                                        end
                                    end
                                    if not cut then
                                        for zdx = -1, 1 do for zdy = -1, 1 do
                                            if (zdx ~= 0 or zdy ~= 0) and not cut then
                                                local zx, zy = nx + zdx, ny + zdy
                                                if Map.GetPlotDistance(nx, ny, zx, zy) == 1 then
                                                    local beside = Map.GetUnitsAt(zx, zy)
                                                    if beside then
                                                        for u3 in beside:Units() do
                                                            if u3:GetOwner() == me then
                                                                local i3 = GameInfo.Units[u3:GetType()]
                                                                if i3 and ((i3.Combat or 0) + (i3.RangedCombat or 0)) > 0 then
                                                                    cut = true
                                                                end
                                                            end
                                                        end
                                                    end
                                                end
                                            end
                                        end end
                                    end
                                    if cut then covered = covered + 1
                                    else table.insert(openHexes, nx .. "," .. ny) end
                                end
                            end
                        end end
                        -- Idle strength within reach. The supply lever above is only pullable if
                        -- somebody can walk onto the open hexes, and the cost of not checking is
                        -- measured: at 沃罗涅什 and 喀山 the count never left 3/6 and 1/6 while
                        -- Catapults "fortified in place because the corridor is jammed" (T155) and
                        -- the pools healed back. A unit that still has movement and is within three
                        -- tiles is exactly the unit that could be doing it, so it is counted here
                        -- with the game's own distance function rather than by hand.
                        local idle = 0
                        for _, u4 in Players[me]:GetUnits():Members() do
                            local ux4, uy4 = u4:GetX(), u4:GetY()
                            if ux4 ~= -9999 and u4:GetMovesRemaining() > 0 then
                                local i4 = GameInfo.Units[u4:GetType()]
                                if i4 and ((i4.Combat or 0) + (i4.RangedCombat or 0) + (i4.Bombard or 0)) > 0
                                    and Map.GetPlotDistance(ux4, uy4, cx, cy) <= 3 then
                                    idle = idle + 1
                                end
                            end
                        end
                        print("CAPTURE_READY|" .. cName .. "|" .. cx .. "," .. cy
                            .. "|hp:" .. cHP .. "|max:" .. cMax
                            .. "|walls:" .. wHP .. "/" .. wMax
                            .. "|owner:" .. pid
                            .. "|melee_adjacent:" .. adj .. "|melee_within_2:" .. near
                            .. "|supply:" .. covered .. "/" .. total
                            .. "|idle3:" .. idle
                            .. "|open:" .. table.concat(openHexes, ";")
                            .. "|" .. who)
                    end
                end
            end)
        end
    end
end
print("{SENTINEL}")
""".replace("{SENTINEL}", SENTINEL)


def parse_capture_readiness_response(lines: list[str]) -> list[CaptureReadiness]:
    """``CAPTURE_READY|<name>|<x>,<y>|hp:N|max:N|walls:N/M|owner:N|melee_adjacent:N|melee_within_2:N|supply:C/T|<unit>``."""
    out: list[CaptureReadiness] = []
    for line in lines:
        if not line.startswith("CAPTURE_READY|"):
            continue
        parts = line.split("|")
        if len(parts) < 6:
            continue
        try:
            x_str, y_str = parts[2].split(",")
            x, y = int(x_str), int(y_str)
        except ValueError:
            continue

        def number(token: str, default: int = 0) -> int:
            try:
                return int(token.split(":", 1)[1])
            except (IndexError, ValueError):
                return default

        walls = parts[5].split(":", 1)[-1] if len(parts) > 5 else "0/0"
        try:
            wall_hp, wall_max = (int(v) for v in walls.split("/", 1))
        except ValueError:
            wall_hp, wall_max = 0, 0
        # `supply:C/T` was added after the melee counts; a line from an older build simply has the
        # unit name there, so both shapes are accepted. `idle3:N` came later again, and is looked
        # for by name so a line without it is read as zero rather than shifting the unit name.
        # `open:x,y;x,y` names the hexes the city is still healing from, which is what turns the
        # supply-line metric into an order the agent can execute.
        supply_covered, supply_total, unit_name, idle_within_3 = 0, 0, "", 0
        open_hexes: list[str] = []
        if len(parts) > 9 and parts[9].startswith("supply:"):
            try:
                covered, total = parts[9].split(":", 1)[1].split("/", 1)
                supply_covered, supply_total = int(covered), int(total)
            except ValueError:
                supply_covered, supply_total = 0, 0
            rest = parts[10:]
            for token in rest:
                if token.startswith("idle3:"):
                    idle_within_3 = number(token)
                elif token.startswith("open:"):
                    open_hexes = [
                        hex_ for hex_ in token.split(":", 1)[1].split(";") if hex_
                    ]
            unit_name = next(
                (t for t in rest if not t.startswith(("idle3:", "open:"))), ""
            )
        elif len(parts) > 9:
            unit_name = parts[9]
        out.append(
            CaptureReadiness(
                city_name=parts[1],
                x=x,
                y=y,
                hp=number(parts[3]) if len(parts) > 3 else 0,
                max_hp=number(parts[4]) if len(parts) > 4 else 0,
                wall_hp=wall_hp,
                wall_max=wall_max,
                melee_adjacent=number(parts[7]) if len(parts) > 7 else 0,
                melee_within_2=number(parts[8]) if len(parts) > 8 else 0,
                supply_covered=supply_covered,
                supply_total=supply_total,
                supply_open_hexes=open_hexes,
                idle_within_3=idle_within_3,
                melee_unit=unit_name,
            )
        )
    return out


def build_skip_remaining_units() -> str:
    """Skip all units with moves remaining (GameCore context —FinishMoves for each)."""
    return """
local me = Game.GetLocalPlayer()
local count = 0
for _, unit in Players[me]:GetUnits():Members() do
    local x = unit:GetX()
    if x ~= -9999 and unit:GetMovesRemaining() > 0 then
        UnitManager.FinishMoves(unit)
        count = count + 1
    end
end
print("OK:SKIPPED|" .. count .. " units")
print("{SENTINEL}")
""".replace("{SENTINEL}", SENTINEL)


def build_automate_explore(unit_index: int) -> str:
    """Automate a unit's exploration (InGame context)."""
    return f"""
{_lua_get_unit(unit_index)}
local hash = GameInfo.UnitOperations["UNITOPERATION_AUTOMATE_EXPLORE"].Hash
if not UnitManager.CanStartOperation(unit, hash, nil, nil) then
    {_bail("ERR:CANNOT_AUTOMATE|Unit cannot auto-explore")}
end
UnitManager.RequestOperation(unit, hash, {{}})
print("OK:AUTOMATED|" .. unit:GetX() .. "," .. unit:GetY())
print("{SENTINEL}")
"""


def build_heal_unit(unit_index: int) -> str:
    """Fortify until healed (InGame context). Distinct from plain fortify."""
    return f"""
{_lua_get_unit(unit_index)}
local hp = unit:GetMaxDamage() - unit:GetDamage()
local maxHP = unit:GetMaxDamage()
if hp >= maxHP then {_bail_lua('"ERR:FULL_HP|Unit already at full health (" .. hp .. "/" .. maxHP .. ")"')} end
local healHash = GameInfo.UnitOperations["UNITOPERATION_HEAL"].Hash
if UnitManager.CanStartOperation(unit, healHash, nil, nil) then
    UnitManager.RequestOperation(unit, healHash, {{}})
    print("OK:HEALING|HP:" .. hp .. "/" .. maxHP)
else
    {_bail("ERR:CANNOT_HEAL|Unit cannot fortify-until-healed")}
end
print("{SENTINEL}")
"""


def build_alert_unit(unit_index: int) -> str:
    """Put unit on alert —sleeps but auto-wakes when enemy enters sight (InGame context)."""
    return f"""
{_lua_get_unit(unit_index)}
if UnitManager.CanStartOperation(unit, UnitOperationTypes.ALERT, nil, nil) then
    UnitManager.RequestOperation(unit, UnitOperationTypes.ALERT, {{}})
    print("OK:ALERT|" .. unit:GetX() .. "," .. unit:GetY())
else
    {_bail("ERR:CANNOT_ALERT|Unit cannot be put on alert")}
end
print("{SENTINEL}")
"""


def build_sleep_unit(unit_index: int) -> str:
    """Put unit to sleep —stays until manually woken (InGame context)."""
    return f"""
{_lua_get_unit(unit_index)}
local sleepHash = GameInfo.UnitOperations["UNITOPERATION_SLEEP"].Hash
if UnitManager.CanStartOperation(unit, sleepHash, nil, nil) then
    UnitManager.RequestOperation(unit, sleepHash, {{}})
    print("OK:SLEEPING|" .. unit:GetX() .. "," .. unit:GetY())
else
    {_bail("ERR:CANNOT_SLEEP|Unit cannot sleep")}
end
print("{SENTINEL}")
"""


def build_delete_unit(unit_index: int) -> str:
    """Delete (disband) a unit (InGame context)."""
    return f"""
{_lua_get_unit(unit_index)}
local unitInfo = GameInfo.Units[unit:GetType()]
local uName = unitInfo and unitInfo.UnitType or "UNKNOWN"
if UnitManager.CanStartCommand(unit, UnitCommandTypes.DELETE, true) then
    UnitManager.RequestCommand(unit, UnitCommandTypes.DELETE)
    print("OK:DELETED|" .. uName .. " at " .. unit:GetX() .. "," .. unit:GetY())
else
    {_bail("ERR:CANNOT_DELETE|Unit cannot be deleted")}
end
print("{SENTINEL}")
"""


def build_improve_tile(unit_index: int, improvement_name: str) -> str:
    """Build an improvement with a builder unit (InGame context).

    improvement_name is e.g. IMPROVEMENT_FARM, IMPROVEMENT_MINE, etc.
    """
    return f"""
{_lua_get_unit(unit_index)}
local imp = GameInfo.Improvements["{improvement_name}"]
if imp == nil then
    -- Feature removals (IMPROVEMENT_REMOVE_*) may not be in Improvements table.
    -- Try scanning by ImprovementType name in case indexed lookup fails.
    for row in GameInfo.Improvements() do
        if row.ImprovementType == "{improvement_name}" then imp = row; break end
    end
    if imp == nil then
        -- List all available improvements so the agent can find the correct name
        local available = {{}}
        local params0 = {{}}
        params0[UnitOperationTypes.PARAM_X] = unit:GetX()
        params0[UnitOperationTypes.PARAM_Y] = unit:GetY()
        for row in GameInfo.Improvements() do
            if row.Buildable then
                params0[UnitOperationTypes.PARAM_IMPROVEMENT_TYPE] = row.Hash
                local ok2, canBuild2 = pcall(function()
                    return UnitManager.CanStartOperation(unit, UnitOperationTypes.BUILD_IMPROVEMENT, nil, params0)
                end)
                if ok2 and canBuild2 then table.insert(available, row.ImprovementType) end
            end
        end
        local hint = #available > 0 and ". Available here: " .. table.concat(available, ", ") or ""
        {_bail_lua(f'"ERR:IMPROVEMENT_NOT_FOUND|{improvement_name} not in game database" .. hint')}
    end
end
local plot = Map.GetPlot(unit:GetX(), unit:GetY())
if plot:GetOwner() ~= me then {_bail_lua('"ERR:NOT_YOUR_TERRITORY|Tile at " .. unit:GetX() .. "," .. unit:GetY() .. " is not in your territory"')} end
local params = {{}}
params[UnitOperationTypes.PARAM_X] = unit:GetX()
params[UnitOperationTypes.PARAM_Y] = unit:GetY()
params[UnitOperationTypes.PARAM_IMPROVEMENT_TYPE] = imp.Hash
if plot:IsImprovementPillaged() then
    local repairHash = GameInfo.UnitOperations["UNITOPERATION_REPAIR"] and GameInfo.UnitOperations["UNITOPERATION_REPAIR"].Hash
    if repairHash then
        local rParams = {{}}
        rParams[UnitOperationTypes.PARAM_X] = unit:GetX()
        rParams[UnitOperationTypes.PARAM_Y] = unit:GetY()
        -- Include improvement type —REPAIR may need to know WHICH improvement to restore
        local impType = plot:GetImprovementType()
        if impType >= 0 then
            local impRow = GameInfo.Improvements[impType]
            if impRow then rParams[UnitOperationTypes.PARAM_IMPROVEMENT_TYPE] = impRow.Hash end
        end
        local canRepair = UnitManager.CanStartOperation(unit, repairHash, nil, rParams)
        if canRepair then
            UnitManager.RequestOperation(unit, repairHash, rParams)
            print("OK:REPAIRING|{improvement_name}|" .. unit:GetX() .. "," .. unit:GetY())
            print("{SENTINEL}"); return
        else
            -- CanStartOperation is unreliable (stale InGame state) —attempt anyway
            pcall(function() UnitManager.RequestOperation(unit, repairHash, rParams) end)
            -- Check if it worked by re-reading pillage state next frame
            print("WARN:REPAIR_ATTEMPTED|CanStartOperation=false but RequestOperation sent. Verify next turn.")
            print("{SENTINEL}"); return
        end
    end
end
if unit:GetMovesRemaining() <= 0 then
    print("ERR:CANNOT_IMPROVE|Builder has no moves remaining this turn")
    print("{SENTINEL}"); return
end
local canBuild, opResult = UnitManager.CanStartOperation(unit, UnitOperationTypes.BUILD_IMPROVEMENT, nil, params, true)
if not canBuild then
    local reasons = {{}}
    if opResult and opResult.FailureReasons then
        for _, r in ipairs(opResult.FailureReasons) do
            table.insert(reasons, tostring(r))
        end
    end
    local reasonStr = #reasons > 0 and table.concat(reasons, "; ") or "unknown reason"
    -- Add diagnostic context
    local diag = {{}}
    local charges = unit:GetBuildCharges()
    if charges <= 0 then
        table.insert(diag, "builder has 0 charges (will be consumed)")
    end
    local existImp = plot:GetImprovementType()
    if existImp >= 0 then
        local eiRow = GameInfo.Improvements[existImp]
        table.insert(diag, "tile already has " .. (eiRow and eiRow.ImprovementType or "improvement"))
    end
    local fType = plot:GetFeatureType()
    if fType >= 0 then
        local fInfo = GameInfo.Features[fType]
        local fName = fInfo and fInfo.FeatureType or "UNKNOWN"
        table.insert(diag, "tile has " .. fName .. " (use remove_feature first)")
    end
    -- List what CAN be built here
    local alts = {{}}
    for altImp in GameInfo.Improvements() do
        if altImp.Buildable and not altImp.TraitType then
            local aParams = {{}}
            aParams[UnitOperationTypes.PARAM_X] = unit:GetX()
            aParams[UnitOperationTypes.PARAM_Y] = unit:GetY()
            aParams[UnitOperationTypes.PARAM_IMPROVEMENT_TYPE] = altImp.Hash
            local ok3, canAlt = pcall(function()
                return UnitManager.CanStartOperation(unit, UnitOperationTypes.BUILD_IMPROVEMENT, nil, aParams)
            end)
            if ok3 and canAlt then table.insert(alts, altImp.ImprovementType) end
        end
    end
    if #alts > 0 then
        table.insert(diag, "can build here: " .. table.concat(alts, ", "))
    else
        table.insert(diag, "no improvements can be built on this tile")
    end
    local diagStr = #diag > 0 and ". " .. table.concat(diag, ". ") or ""
    print("ERR:CANNOT_IMPROVE|" .. reasonStr .. diagStr .. ". Builder at " .. unit:GetX() .. "," .. unit:GetY())
    print("{SENTINEL}"); return
end
UnitManager.RequestOperation(unit, UnitOperationTypes.BUILD_IMPROVEMENT, params)
print("OK:IMPROVING|{improvement_name}|" .. unit:GetX() .. "," .. unit:GetY())
print("{SENTINEL}")
"""


def build_remove_feature(unit_index: int) -> str:
    """Remove (chop/harvest) a feature from the tile the builder is standing on.

    Uses UNITOPERATION_REMOVE_FEATURE - works on forest, jungle, marsh. The game auto-detects which
    feature is present; no feature param needed.

    **The refusal now names the missing prerequisite, because the bare one cost two attempts a wrong
    finding.** A feature is only removable once its `RemoveTech` is researched
    (`Base/Assets/Gameplay/Data/Features.xml`: `FEATURE_FOREST` -> `TECH_MINING`, `FEATURE_JUNGLE` ->
    `TECH_BRONZE_WORKING`, `FEATURE_MARSH` -> `TECH_IRRIGATION`), so `UnitManager.CanStartOperation`
    legitimately refuses the other two until then. The old message said only
    `ERR:CANNOT_REMOVE|Cannot remove FEATURE_JUNGLE at (x,y)`, which reads as "the tool cannot chop
    jungle"; attempt A5 recorded exactly that as a defect, and A2 had recorded the same thing at its
    T26. Both were the tech line: A5 held Mining from T8 and chopped forest twice, and its jungle
    attempts at T39 and T42 were both before Bronze Working (owned T45). The message now says which
    tech is missing, and says so plainly when the tech is present and something else refused.
    """
    return f"""
{_lua_get_unit(unit_index)}
if unit:GetMovesRemaining() <= 0 then
    {_bail("ERR:NO_MOVES|Builder has no moves remaining this turn")}
end
local plot = Map.GetPlot(unit:GetX(), unit:GetY())
local fType = plot:GetFeatureType()
if fType < 0 then
    {_bail_lua('"ERR:NO_FEATURE|No feature on tile (" .. unit:GetX() .. "," .. unit:GetY() .. ") to remove"')}
end
local fInfo = GameInfo.Features[fType]
local fName = fInfo and fInfo.FeatureType or "UNKNOWN"
local opRow = GameInfo.UnitOperations["UNITOPERATION_REMOVE_FEATURE"]
if not opRow then
    {_bail("ERR:OP_NOT_FOUND|UNITOPERATION_REMOVE_FEATURE not available")}
end
local params = {{}}
params[UnitOperationTypes.PARAM_X] = unit:GetX()
params[UnitOperationTypes.PARAM_Y] = unit:GetY()
local canStart = UnitManager.CanStartOperation(unit, opRow.Hash, nil, params, true)
if not canStart then
    -- Say WHY. The feature's own RemoveTech is the usual reason (Features.xml), and a refusal that
    -- does not name it is read as a tool defect - which it was, twice.
    local reason = " - the feature names no removal technology, so the refusal is something else"
    local reqTech = fInfo and fInfo.RemoveTech or nil
    if reqTech and reqTech ~= "" then
        local techRow = GameInfo.Technologies[reqTech]
        local techName = techRow and Locale.Lookup(techRow.Name) or reqTech
        local has = false
        pcall(function() has = Players[me]:GetTechs():HasTech(techRow.Index) end)
        if has then
            reason = " - " .. techName .. " (" .. reqTech .. ") IS researched, so the refusal is something else: moves, terrain, or an enemy on the tile"
        else
            reason = " - removing " .. fName .. " needs " .. techName .. " (" .. reqTech .. "), which this empire has not researched"
        end
    end
    {_bail_lua('"ERR:CANNOT_REMOVE|Cannot remove " .. fName .. " at (" .. unit:GetX() .. "," .. unit:GetY() .. ")" .. reason')}
end
UnitManager.RequestOperation(unit, opRow.Hash, params)
print("OK:REMOVING_FEATURE|" .. fName .. " at " .. unit:GetX() .. "," .. unit:GetY())
print("{SENTINEL}")
"""


def build_repair_improvement(unit_index: int) -> str:
    """Repair a pillaged improvement at the builder's current tile (InGame context).

    Auto-detects the pillaged improvement —no improvement name needed.
    """
    return f"""
{_lua_get_unit(unit_index)}
local ux, uy = unit:GetX(), unit:GetY()
if unit:GetMovesRemaining() <= 0 then
    {_bail("ERR:NO_MOVES|Builder has no moves remaining this turn")}
end
local plot = Map.GetPlot(ux, uy)
if not plot then {_bail("ERR:NO_PLOT|Invalid plot")} end
local impType = plot:GetImprovementType()
if impType < 0 then
    {_bail_lua('"ERR:NO_IMPROVEMENT|No improvement on tile (" .. ux .. "," .. uy .. ") to repair"')}
end
local okPil, isPillaged = pcall(function() return plot:IsImprovementPillaged() end)
if not okPil or not isPillaged then
    local impInfo = GameInfo.Improvements[impType]
    local impName = impInfo and impInfo.ImprovementType or "UNKNOWN"
    {_bail_lua('"ERR:NOT_PILLAGED|" .. impName .. " at (" .. ux .. "," .. uy .. ") is not pillaged"')}
end
local impInfo = GameInfo.Improvements[impType]
local impName = impInfo and impInfo.ImprovementType or "UNKNOWN"
local repairOp = GameInfo.UnitOperations["UNITOPERATION_REPAIR"]
if not repairOp then {_bail("ERR:OP_NOT_FOUND|UNITOPERATION_REPAIR not available")} end
local rParams = {{}}
rParams[UnitOperationTypes.PARAM_X] = ux
rParams[UnitOperationTypes.PARAM_Y] = uy
if impInfo then rParams[UnitOperationTypes.PARAM_IMPROVEMENT_TYPE] = impInfo.Hash end
local canRepair = UnitManager.CanStartOperation(unit, repairOp.Hash, nil, rParams)
if canRepair then
    UnitManager.RequestOperation(unit, repairOp.Hash, rParams)
    print("OK:REPAIRING|" .. impName .. " at (" .. ux .. "," .. uy .. ")")
else
    pcall(function() UnitManager.RequestOperation(unit, repairOp.Hash, rParams) end)
    print("WARN:REPAIR_ATTEMPTED|CanStartOperation=false but RequestOperation sent for " .. impName .. " at (" .. ux .. "," .. uy .. "). Verify next turn.")
end
print("{SENTINEL}")
"""


def build_remove_improvement(unit_index: int) -> str:
    """Remove (demolish) an intact improvement from the builder's current tile.

    Uses UNITOPERATION_REMOVE_IMPROVEMENT. The game auto-detects which
    improvement is present; no improvement param needed. Costs one builder charge.
    """
    return f"""
{_lua_get_unit(unit_index)}
local ux, uy = unit:GetX(), unit:GetY()
if unit:GetMovesRemaining() <= 0 then
    {_bail("ERR:NO_MOVES|Builder has no moves remaining this turn")}
end
local plot = Map.GetPlot(ux, uy)
if not plot then {_bail("ERR:NO_PLOT|Invalid plot")} end
local impType = plot:GetImprovementType()
if impType < 0 then
    {_bail_lua('"ERR:NO_IMPROVEMENT|No improvement on tile (" .. ux .. "," .. uy .. ") to remove"')}
end
local impInfo = GameInfo.Improvements[impType]
local impName = impInfo and impInfo.ImprovementType or "UNKNOWN"
local opRow = GameInfo.UnitOperations["UNITOPERATION_REMOVE_IMPROVEMENT"]
if not opRow then
    {_bail("ERR:OP_NOT_FOUND|UNITOPERATION_REMOVE_IMPROVEMENT not available in this game version")}
end
local params = {{}}
params[UnitOperationTypes.PARAM_X] = ux
params[UnitOperationTypes.PARAM_Y] = uy
local canStart = UnitManager.CanStartOperation(unit, opRow.Hash, nil, params, true)
if not canStart then
    {_bail_lua('"ERR:CANNOT_REMOVE|Cannot remove " .. impName .. " at (" .. ux .. "," .. uy .. "). Builder must be on the tile with moves and charges."')}
end
UnitManager.RequestOperation(unit, opRow.Hash, params)
print("OK:REMOVING_IMPROVEMENT|" .. impName .. " at (" .. ux .. "," .. uy .. ")")
print("{SENTINEL}")
"""


def build_sacrifice_builder_charges(unit_index: int) -> str:
    """Sacrifice builder charges to boost a district project (Royal Society).

    Requires the Royal Society (BUILDING_GOV_SCIENCE) to be built.
    Builder must be on the district tile where a project is actively building.
    Consumes ALL remaining charges. Once per city per turn.
    Each charge adds 2% of the project's production cost.
    """
    return f"""
{_lua_get_unit(unit_index)}
local entry = GameInfo.Units[unit:GetType()]
if not entry or entry.UnitType ~= "UNIT_BUILDER" then {_bail("ERR:NOT_A_BUILDER|Unit is not a builder")} end
local ux, uy = unit:GetX(), unit:GetY()
local charges = unit:GetBuildCharges()
if charges <= 0 then {_bail("ERR:NO_CHARGES|Builder has no charges remaining")} end
if unit:GetMovesRemaining() <= 0 then {_bail("ERR:NO_MOVES|Builder has no moves remaining this turn")} end
-- Verify Royal Society exists
local hasRS = false
local rsIdx = GameInfo.Buildings["BUILDING_GOV_SCIENCE"] and GameInfo.Buildings["BUILDING_GOV_SCIENCE"].Index
if rsIdx then
    for _, city in Players[me]:GetCities():Members() do
        if city:GetBuildings():HasBuilding(rsIdx) then hasRS = true; break end
    end
end
if not hasRS then {_bail("ERR:NO_ROYAL_SOCIETY|Royal Society (Tier 3 government building) required")} end
-- Check builder is on a district tile
local plot = Map.GetPlot(ux, uy)
local distType = plot:GetDistrictType()
if distType < 0 then
    {_bail_lua('"ERR:NOT_ON_DISTRICT|Builder at (" .. ux .. "," .. uy .. ") is not on a district tile. Move to the district with an active project."')}
end
local dInfo = GameInfo.Districts[distType]
local dName = dInfo and dInfo.DistrictType or "UNKNOWN"
-- Find the city owning this plot and check for active project
local cityOwner = nil
for _, city in Players[me]:GetCities():Members() do
    for _, d in city:GetDistricts():Members() do
        if d:GetX() == ux and d:GetY() == uy then cityOwner = city; break end
    end
    if cityOwner then break end
end
if not cityOwner then {_bail("ERR:NO_CITY|Could not find city owning this district")} end
local bq = cityOwner:GetBuildQueue()
local producing = "nothing"
local okProd, currentHash = pcall(function() return bq:GetCurrentProductionTypeHash() end)
if okProd and currentHash then
    for proj in GameInfo.Projects() do
        if proj.Hash == currentHash then producing = proj.ProjectType; break end
    end
end
if producing == "nothing" then
    {_bail_lua('"ERR:NO_PROJECT|" .. Locale.Lookup(cityOwner:GetName()) .. " is not building a project. Queue a project first."')}
end
-- Execute the command
local cmdRow = GameInfo.UnitCommands["UNITCOMMAND_PROJECT_PRODUCTION"]
if not cmdRow then {_bail("ERR:CMD_NOT_FOUND|UNITCOMMAND_PROJECT_PRODUCTION not in game database")} end
local cmdHash = cmdRow.Hash
local can, failTable = UnitManager.CanStartCommand(unit, cmdHash, nil, true)
if not can then
    local reasons = {{}}
    if failTable then
        for _, v in pairs(failTable) do
            if type(v) == "table" then
                for _, s in pairs(v) do
                    if type(s) == "string" and s ~= "" then table.insert(reasons, s) end
                end
            end
        end
    end
    local reasonStr = #reasons > 0 and table.concat(reasons, "; ") or "unknown"
    {_bail_lua('"ERR:CANNOT_SACRIFICE|" .. reasonStr .. ". Builder at (" .. ux .. "," .. uy .. ") on " .. dName .. " with " .. charges .. " charges, city building " .. producing')}
end
-- Try with coordinate params first
local tParams = {{}}
tParams[UnitCommandTypes.PARAM_X] = ux
tParams[UnitCommandTypes.PARAM_Y] = uy
UnitManager.RequestCommand(unit, cmdHash, tParams)
-- Verify charges were consumed
local newCharges = unit:GetBuildCharges()
if newCharges == charges then
    -- Fallback: try with empty params
    UnitManager.RequestCommand(unit, cmdHash, {{}})
    newCharges = unit:GetBuildCharges()
end
if newCharges == charges then
    -- Second fallback: try RequestCommandImmediate
    pcall(function() UnitManager.RequestCommandImmediate(unit, cmdHash, tParams) end)
    newCharges = unit:GetBuildCharges()
end
if newCharges < charges then
    local consumed = charges - newCharges
    print("OK:SACRIFICED|" .. consumed .. " charges consumed for " .. producing .. " in " .. Locale.Lookup(cityOwner:GetName()) .. " at (" .. ux .. "," .. uy .. ") on " .. dName)
else
    print("WARN:SACRIFICE_UNCERTAIN|Command sent but charges unchanged (" .. charges .. "). Builder at (" .. ux .. "," .. uy .. ") on " .. dName .. ", city building " .. producing .. ". Ensure builder is on the exact district tile where the project's district is located.")
end
print("{SENTINEL}")
"""


def build_build_route(unit_index: int) -> str:
    """Build a route (road/railroad) on the Military Engineer's current tile.

    Uses UNITOPERATION_BUILD_ROUTE —after Steam Power tech this builds
    railroads (route type 4).  Does NOT consume charges.  Costs 1 Iron +
    1 Coal per railroad tile from the player's stockpile.
    """
    return f"""
{_lua_get_unit(unit_index)}
if unit:GetMovesRemaining() <= 0 then
    {_bail("ERR:NO_MOVES|Military Engineer has no moves remaining this turn")}
end
local x, y = unit:GetX(), unit:GetY()
local plot = Map.GetPlot(x, y)
if not plot or plot:GetOwner() ~= me then
    {_bail_lua('"ERR:NOT_YOUR_TERRITORY|Tile (" .. x .. "," .. y .. ") is not in your territory"')}
end
local opRow = GameInfo.UnitOperations["UNITOPERATION_BUILD_ROUTE"]
if not opRow then
    {_bail("ERR:OP_NOT_FOUND|UNITOPERATION_BUILD_ROUTE not in game database")}
end
local params = {{}}
params[UnitOperationTypes.PARAM_X] = x
params[UnitOperationTypes.PARAM_Y] = y
local canStart = UnitManager.CanStartOperation(unit, opRow.Hash, nil, params, true)
if not canStart then
    local rt = plot:GetRouteType()
    local reason = "unknown reason"
    if rt == 4 then reason = "tile already has a railroad"
    elseif plot:IsCity() then reason = "cannot build on city center"
    end
    {_bail_lua('"ERR:CANNOT_BUILD_ROUTE|" .. reason .. " at (" .. x .. "," .. y .. ")"')}
end
UnitManager.RequestOperation(unit, opRow.Hash, params)
-- Read back route type (may be stale same-frame, but try)
local newRoute = plot:GetRouteType()
local routeName = "ROUTE"
if newRoute == 4 then routeName = "RAILROAD"
elseif newRoute >= 0 then routeName = "ROAD"
end
print("OK:BUILT_" .. routeName .. "|" .. x .. "," .. y)
print("{SENTINEL}")
"""


def parse_units_response(lines: list[str]) -> list[UnitInfo]:
    units = []
    for line in lines:
        parts = line.split("|")
        if len(parts) < 7:
            continue
        x_str, y_str = parts[4].split(",")
        moves_cur, moves_max = parts[5].split("/")
        hp_cur, hp_max = parts[6].split("/")
        cs = int(parts[7]) if len(parts) > 7 else 0
        rs = int(parts[8]) if len(parts) > 8 else 0
        charges = int(parts[9]) if len(parts) > 9 else 0
        targets_raw = parts[10] if len(parts) > 10 else ""
        targets = [t for t in targets_raw.split(";") if t] if targets_raw else []
        needs_promo = parts[11] == "1" if len(parts) > 11 else False
        can_upgrade = parts[12] == "1" if len(parts) > 12 else False
        upgrade_target = parts[13] if len(parts) > 13 else ""
        upgrade_cost = int(parts[14]) if len(parts) > 14 and parts[14].isdigit() else 0
        valid_imps_raw = parts[15] if len(parts) > 15 else ""
        valid_imps = (
            [v for v in valid_imps_raw.split(";") if v] if valid_imps_raw else []
        )
        religion = parts[16] if len(parts) > 16 else ""
        # Appended after `religion`, so a log written before these columns parses as before:
        # an absent activity reads "?" (unknown) rather than "awake", which is the safe direction.
        activity = parts[17] if len(parts) > 17 else ""
        fortify_turns = (
            int(parts[18]) if len(parts) > 18 and parts[18].lstrip("-").isdigit() else 0
        )
        ready_to_move = (parts[19] == "1") if len(parts) > 19 else True
        units.append(
            UnitInfo(
                unit_id=int(parts[0]),
                unit_index=int(parts[1]),
                name=parts[2],
                unit_type=parts[3],
                x=int(x_str),
                y=int(y_str),
                moves_remaining=float(moves_cur),
                max_moves=float(moves_max),
                health=int(hp_cur),
                max_health=int(hp_max),
                combat_strength=cs,
                ranged_strength=rs,
                build_charges=charges,
                targets=targets,
                needs_promotion=needs_promo,
                can_upgrade=can_upgrade,
                upgrade_target=upgrade_target,
                upgrade_cost=upgrade_cost,
                valid_improvements=valid_imps,
                religion=religion,
                activity=activity,
                fortify_turns=fortify_turns,
                ready_to_move=ready_to_move,
            )
        )
    return units


def parse_religious_sightings(lines: list[str]) -> list[ReligiousSighting]:
    """Parse the `RELIGIOUS|` rows of the threat scan into `ReligiousSighting` records.

    Separate from the `THREAT|` rows on purpose: those feed the contact metrics (`enemies_within_2`,
    `enemies_cavalry_within_2`, `local_superiority`), and a religious unit counted there would move
    numbers that decide attacks. These rows exist to be *seen*, not to be fought by arithmetic.
    """
    out: list[ReligiousSighting] = []
    for line in lines:
        parts = line.split("|")
        if not line.startswith("RELIGIOUS|") or len(parts) < 6:
            continue
        xy = parts[4].split(",")
        hp, _, max_hp = parts[5].partition("/")
        fields: dict[str, str] = {}
        for token in parts[6:]:
            key, _, value = token.partition(":")
            fields[key] = value
        out.append(
            ReligiousSighting(
                player_id=int(_number(parts[1], -1)),
                owner_name=parts[2],
                unit_type=parts[3],
                x=int(_number(xy[0])),
                y=int(_number(xy[1])),
                hp=int(_number(hp)),
                max_hp=int(_number(max_hp, 100)),
                religious_strength=int(_number(fields.get("rstr", "0"))),
                distance=int(_number(fields.get("dist", "999"), 999)),
                unit_distance=int(_number(fields.get("udist", "999"), 999)),
                at_war=fields.get("atwar") == "1",
            )
        )
    return out


def parse_threat_scan_response(lines: list[str]) -> list[ThreatInfo]:
    threats: list[ThreatInfo] = []
    for line in lines:
        if not line.startswith("THREAT|"):
            continue
        parts = line.split("|")
        # Format: THREAT|owner_id|owner_name|unit_type|x,y|hp/max|CS:n|RS:n|dist:n|cs:0/1|uid:N|pc:PROMOTION_CLASS_X|udist:n|near:n|adj:n
        if len(parts) >= 9:
            x_str, y_str = parts[4].split(",")
            hp_str, max_str = parts[5].split("/")
            cs = int(parts[6].replace("CS:", "")) if parts[6].startswith("CS:") else 0
            rs = int(parts[7].replace("RS:", "")) if parts[7].startswith("RS:") else 0
            dist = (
                int(parts[8].replace("dist:", ""))
                if parts[8].startswith("dist:")
                else 0
            )
            uid = 0
            if len(parts) > 10 and parts[10].startswith("uid:"):
                uid = int(parts[10][4:])
            pc = ""
            if len(parts) > 11 and parts[11].startswith("pc:"):
                pc = parts[11][3:]
            udist = 999
            if len(parts) > 12 and parts[12].startswith("udist:"):
                udist = int(parts[12][6:])
            near = 0
            if len(parts) > 13 and parts[13].startswith("near:"):
                near = int(parts[13][5:])
            adj = 0
            if len(parts) > 14 and parts[14].startswith("adj:"):
                adj = int(parts[14][4:])
            threats.append(
                ThreatInfo(
                    unit_type=parts[3],
                    x=int(x_str),
                    y=int(y_str),
                    hp=int(hp_str),
                    max_hp=int(max_str),
                    combat_strength=cs,
                    ranged_strength=rs,
                    distance=dist,
                    owner_id=int(parts[1]),
                    owner_name=parts[2],
                    is_city_state=len(parts) > 9
                    and parts[9].startswith("cs:")
                    and parts[9][3:] == "1",
                    unit_id=uid,
                    promotion_class=pc,
                    unit_distance=udist,
                    friendly_within_2=near,
                    friendly_within_1=adj,
                )
            )
        elif len(parts) >= 7:
            # Legacy format fallback: THREAT|unit_type|x,y|hp/max|CS:n|RS:n|dist:n
            x_str, y_str = parts[2].split(",")
            hp_str, max_str = parts[3].split("/")
            cs = int(parts[4].replace("CS:", "")) if parts[4].startswith("CS:") else 0
            rs = int(parts[5].replace("RS:", "")) if parts[5].startswith("RS:") else 0
            dist = (
                int(parts[6].replace("dist:", ""))
                if parts[6].startswith("dist:")
                else 0
            )
            threats.append(
                ThreatInfo(
                    unit_type=parts[1],
                    x=int(x_str),
                    y=int(y_str),
                    hp=int(hp_str),
                    max_hp=int(max_str),
                    combat_strength=cs,
                    ranged_strength=rs,
                    distance=dist,
                )
            )
    return threats


def build_fog_neighbor_query(positions: list[tuple[int, int]]) -> str:
    """GameCore: for each position, report which adjacent tiles are in fog."""
    checks = "\n".join(f"check({x},{y})" for x, y in positions)
    return f"""
local me = Game.GetLocalPlayer()
local pVis = PlayersVisibility[me]
local dirNames = {{"NE","E","SE","SW","W","NW"}}
function check(cx, cy)
    local plot = Map.GetPlot(cx, cy)
    if not plot then return end
    local fog = {{}}
    for i = 0, 5 do
        local adj = Map.GetAdjacentPlot(cx, cy, i)
        if adj and not pVis:IsVisible(adj:GetX(), adj:GetY()) then
            table.insert(fog, dirNames[i+1])
        end
    end
    if #fog > 0 then
        print("FOG|" .. cx .. "," .. cy .. "|" .. table.concat(fog, ","))
    end
end
{checks}
print("{SENTINEL}")
"""


def parse_fog_neighbor_response(
    lines: list[str],
) -> dict[tuple[int, int], list[str]]:
    """Parse FOG|x,y|dir1,dir2,... lines into {(x,y): [directions]}."""
    result: dict[tuple[int, int], list[str]] = {}
    for line in lines:
        if not line.startswith("FOG|"):
            continue
        parts = line.split("|")
        x_str, y_str = parts[1].split(",")
        result[(int(x_str), int(y_str))] = parts[2].split(",")
    return result


def diff_threats(
    before: list[ThreatInfo], after: list[ThreatInfo]
) -> tuple[list[ThreatInfo], list[ThreatInfo], list[ThreatInfo]]:
    """Compare threat snapshots: (disappeared, new, moved).

    Match by unit_id when available, otherwise by (owner_id, unit_type, x, y).
    """
    after_by_uid: dict[int, ThreatInfo] = {}
    after_by_key: dict[tuple, ThreatInfo] = {}
    after_matched: set[int] = set()

    for i, t in enumerate(after):
        if t.unit_id:
            after_by_uid[t.unit_id] = t
        after_by_key[(t.owner_id, t.unit_type, t.x, t.y)] = t

    disappeared: list[ThreatInfo] = []
    moved: list[ThreatInfo] = []

    for bt in before:
        at = None
        if bt.unit_id and bt.unit_id in after_by_uid:
            at = after_by_uid[bt.unit_id]
        elif (bt.owner_id, bt.unit_type, bt.x, bt.y) in after_by_key:
            at = after_by_key[(bt.owner_id, bt.unit_type, bt.x, bt.y)]

        if at is None:
            disappeared.append(bt)
        else:
            idx = after.index(at)
            after_matched.add(idx)
            if at.x != bt.x or at.y != bt.y:
                moved.append(at)

    new_threats = [t for i, t in enumerate(after) if i not in after_matched]
    return disappeared, new_threats, moved


# The march: what a path really costs and where the engine actually stops. Two facts the
# tile-count arithmetic (`ceil((#path - reach) / reach)`) cannot see, and this war paid for both
# after the fact:
#
#   * **a tile costs what the map says** - `plot:GetMovementCost()`, the number the game's own
#     tooltip prints (`Base/Assets/UI/ToolTips/PlotToolTip.lua:659`): 1 on flat ground, 2 for Hills
#     or Woods, 3 for Forest on Hills, and a river crossing takes the rest of the turn;
#   * **entering a tile in an enemy's zone of control ends that turn's movement** (manual:875),
#     light and heavy cavalry excepted (manual:735-737) - so one clipped ZOC tile costs a whole
#     turn, which is what `STOPPED_MID_PATH` was reporting after the event (232 of them over
#     T228-T299, and a rule written to excuse the stop rather than predict it).
#
# Which units project a ZOC is the game's own flag and not a guess: `GameInfo.Units[type].ZoneOfControl`
# is `true` for the melee, cavalry and anti-cavalry line (47 of the base game's 71 combat units) and
# `false` for every ranged and siege unit (Archer, Crossbowman, Catapult, Bombard - 24 of 71), so a
# plan may walk past an enemy gun without a stop and must not walk past an enemy Spearman. All 71
# carry the flag explicitly (`Base/Assets/Gameplay/Data/Units.xml`), so `~= false` is the whole test.
#
# Turn 0 is the **engine's own answer**, not a simulation: `UnitManager.GetReachableMovement` already
# accounts for terrain, rivers and ZOC, so the walk follows the engine's path while the engine says
# the tile is reachable and only simulates from the first tile it cannot reach. Later turns are
# walked with the unit's own `GetMaxMoves()` (`Base/Assets/UI/Panels/UnitPanel.lua:2242`) as the
# per-turn budget. Every call sits inside a `pcall`: when an API is unavailable the caller keeps the
# old tile-count arithmetic and reports `cost:-1` / `zoc:-1`, which mean "not known" and never
# "clear".
#
# **What is still an approximation**, and it is stated so nobody reads the number as exact: a river
# crossing and an embarkation spend the whole turn as well (manual:73), and those are modelled only
# on turn 0 - where the engine's reachable set ends the movement for us. On later turns the walk
# pays each tile's terrain cost and stops for ZOC, so a route that crosses a river on turn 2 can
# read one turn short. The per-tile costs, the ZOC stops and the engine's first turn are exact.
#
# The enemy scan sees **visible** enemies only. An unseen ZOC cannot be known, so `zoc:0` means "no
# ZOC we can see on this route" - the same honesty the line-of-sight verdict uses.
_MARCH_HELPER = """
-- Does this unit type project a zone of control? The game's data carries the answer
-- (`ZoneOfControl` in `GameInfo.Units`: true for the melee, cavalry and anti-cavalry line, false
-- for every ranged and siege unit), and a boolean column can come back as `false` **or** as `0`
-- depending on how the row was built, so both are read as "no". A row that does not carry the
-- column at all falls back to the promotion class the ranged and siege lines share - never to
-- "assume it projects", because that would invent a detour past an enemy Archer that is not there.
local function _marchProjectsZoc(info)
    if info == nil then return false end
    local v = nil
    pcall(function() v = info.ZoneOfControl end)
    if v == false or v == 0 then return false end
    if v == true or v == 1 then return true end
    local pc = ""
    pcall(function() pc = info.PromotionClass or "" end)
    if pc == "PROMOTION_CLASS_RANGED" or pc == "PROMOTION_CLASS_SIEGE" then return false end
    return true
end
local _MARCH_ZOC, _MARCH_ZOC_READY = nil, false
local function _marchZoc(me)
    if _MARCH_ZOC_READY then return _MARCH_ZOC end
    _MARCH_ZOC_READY = true
    _MARCH_ZOC = {}
    local vis = PlayersVisibility[me]
    local dip = Players[me]:GetDiplomacy()
    for pid = 0, 63 do
        if pid ~= me and Players[pid] and Players[pid]:IsAlive()
            and (pid == 63 or Players[pid]:IsMajor() or dip:IsAtWarWith(pid)) then
            for _, eu in Players[pid]:GetUnits():Members() do
                local ex, ey = eu:GetX(), eu:GetY()
                if ex ~= -9999 and vis:IsVisible(ex, ey) then
                    local ei = GameInfo.Units[eu:GetType()]
                    local cs = ((ei and ei.Combat) or 0) + ((ei and ei.RangedCombat) or 0)
                        + ((ei and ei.Bombard) or 0)
                    if cs > 0 and _marchProjectsZoc(ei) then
                        for dx = -1, 1 do for dy = -1, 1 do
                            local np = Map.GetPlot(ex + dx, ey + dy)
                            if np and Map.GetPlotDistance(ex, ey, np:GetX(), np:GetY()) == 1 then
                                _MARCH_ZOC[np:GetIndex()] = true
                            end
                        end end
                    end
                end
            end
        end
    end
    return _MARCH_ZOC
end
-- Light and heavy cavalry ignore ZOC (manual:735-737). Compared with `==` on the whole class and
-- never by substring: an anti-cavalry unit carries "CAVALRY" in its PromotionClass too, and a
-- `string.find(pc, "CAVALRY")` would hand a Spearman the exemption.
local function _marchIgnoresZoc(unit)
    local pc = ""
    pcall(function()
        local ei = GameInfo.Units[unit:GetType()]
        pc = (ei and ei.PromotionClass) or ""
    end)
    return pc == "PROMOTION_CLASS_LIGHT_CAVALRY" or pc == "PROMOTION_CLASS_HEAVY_CAVALRY"
end
-- The unit's own per-turn budget, or 0 when the engine will not say (the caller then falls back to
-- the tile-count arithmetic rather than to a number this helper made up).
local function _marchPerTurn(unit)
    local m = 0
    pcall(function() m = unit:GetMaxMoves() end)
    if not m or m <= 0 then return 0 end
    return m
end
local function _marchTileCost(plot)
    local c = 1
    pcall(function() c = plot:GetMovementCost() end)
    if not c or c < 1 then c = 1 end
    return c
end
-- Walk `path` (plot indices) from where `unit` stands. `reachSet` is this turn's reachable set, the
-- engine's own answer for turn 0. Returns turns (0 = this turn), the sum of the tiles' movement
-- costs, how many turns the route ends inside a ZOC, and the first such tile as x, y, turn. Returns
-- nil when the engine will not report the unit's per-turn moves.
local function _marchWalk(me, unit, path, reachSet, perTurn, ignoreZoc)
    if perTurn == nil then perTurn = _marchPerTurn(unit) end
    if perTurn <= 0 then return nil end
    if ignoreZoc == nil then ignoreZoc = _marchIgnoresZoc(unit) end
    local zoc = _marchZoc(me)
    local cost, stops, sx, sy, sturn = 0, 0, -1, -1, -1
    local idx = 1
    while idx <= #path and reachSet[path[idx]] do
        cost = cost + _marchTileCost(Map.GetPlotByIndex(path[idx]))
        idx = idx + 1
    end
    if idx > #path then return 0, cost, 0, -1, -1, -1 end
    local turn, budget = 1, perTurn
    while idx <= #path do
        if budget <= 0 then
            turn = turn + 1
            budget = perTurn
        end
        local plot = Map.GetPlotByIndex(path[idx])
        local c = _marchTileCost(plot)
        cost = cost + c
        budget = budget - c
        if budget < 0 then budget = 0 end
        if zoc[path[idx]] and not ignoreZoc then
            budget = 0
            stops = stops + 1
            if sx < 0 then sx, sy, sturn = plot:GetX(), plot:GetY(), turn end
        end
        idx = idx + 1
    end
    return turn, cost, stops, sx, sy, sturn
end
-- The route tokens an option line carries: `zoc:N`, `cost:N`, and `zocat:x,y,turn` for the first
-- stop. -1 on either means the engine would not say, which is not the same as clear.
local function _marchTokens(cost, zoc, sx, sy, sturn)
    if cost == nil then cost = -1 end
    if zoc == nil then zoc = -1 end
    local s = "|zoc:" .. zoc .. "|cost:" .. cost
    if zoc > 0 and sx and sx >= 0 then
        s = s .. "|zocat:" .. sx .. "," .. sy .. "," .. sturn
    end
    return s
end
"""


def build_pathing_estimate_query(unit_index: int, target_x: int, target_y: int) -> str:
    """InGame context: estimate turns for a unit to reach a destination.

    ``UnitManager.GetMoveToPath`` for the full path, ``GetReachableMovement`` for this turn's
    reachable tiles - and then the walk in `_MARCH_HELPER`, which pays each tile's real movement
    cost and ends a turn where the route enters an enemy zone of control (manual:875). The old
    tile-count arithmetic survives only as the fallback for a game that will not report the unit's
    per-turn moves, and says so (`cost:-1|zoc:-1`).
    """
    return f"""
{_lua_get_unit(unit_index)}
-- Guard: GetMoveToPath returns degenerate paths for units with 0 moves
if unit:GetMovesRemaining() <= 0 then
    print("PATH|-2|0|0")
    print("WAYPOINTS|")
    print("{SENTINEL}")
    return
end
{_MARCH_HELPER}
local targetPlot = Map.GetPlot({target_x}, {target_y})
if not targetPlot then {_bail(f"ERR:INVALID_TARGET|Target ({target_x},{target_y}) is out of bounds")} end
local path = UnitManager.GetMoveToPath(unit, targetPlot:GetIndex())
if not path or #path == 0 then
    print("PATH|-1|0|0")
    print("WAYPOINTS|")
    print("{SENTINEL}")
    return
end
-- Validate path reaches destination (GetMoveToPath returns garbage for unreachable targets)
local lastPlot = Map.GetPlotByIndex(path[#path])
if lastPlot:GetX() ~= {target_x} or lastPlot:GetY() ~= {target_y} then
    print("PATH|-1|" .. #path .. "|0")
    print("WAYPOINTS|")
    print("{SENTINEL}")
    return
end
local reach = UnitManager.GetReachableMovement(unit)
local reachSet = {{}}
if reach then
    for _, pIdx in ipairs(reach) do reachSet[pIdx] = true end
end
-- Count how many path tiles are reachable this turn
local reachCount = 0
for _, pIdx in ipairs(path) do
    if reachSet[pIdx] then reachCount = reachCount + 1 end
end
local totalTiles = #path
-- The walk replaces the tile-count arithmetic: real per-tile cost, and the turn a ZOC stop costs.
-- `reachCount` is still printed - it is the engine's own answer for this turn and older callers
-- read it - and it is still the fallback when the engine will not report the unit's per-turn moves.
local walkTurns, walkCost, walkZoc, walkSx, walkSy, walkSturn = _marchWalk(me, unit, path, reachSet)
local turnsNeeded
if walkTurns ~= nil then
    turnsNeeded = walkTurns
else
    walkCost, walkZoc = -1, -1
    if reachCount >= totalTiles then
        turnsNeeded = 0
    else
        turnsNeeded = math.ceil((totalTiles - reachCount) / math.max(reachCount, 1))
    end
end
print("PATH|" .. turnsNeeded .. "|" .. totalTiles .. "|" .. reachCount
    .. "|" .. walkCost .. "|" .. walkZoc)
if walkZoc ~= nil and walkZoc > 0 and walkSx >= 0 then
    -- Where the route ends a turn inside an enemy ZOC (manual:875). A light or heavy cavalry unit
    -- never produces one: it ignores ZOC (manual:735-737).
    print("ZOCSTOP|" .. walkSx .. "," .. walkSy .. "|" .. walkSturn)
end
-- Emit waypoints for context (first tile, last reachable, destination)
local waypoints = {{}}
for i, pIdx in ipairs(path) do
    local plot = Map.GetPlotByIndex(pIdx)
    waypoints[#waypoints + 1] = "(" .. plot:GetX() .. "," .. plot:GetY() .. ")"
end
print("WAYPOINTS|" .. table.concat(waypoints, ";"))
print("{SENTINEL}")
"""


def parse_pathing_estimate(lines: list[str]) -> PathingEstimate:
    """Parse ``PATH|``, ``WAYPOINTS|`` and ``ZOCSTOP|`` output.

    The ``PATH`` line carries two more fields than it used to (the walk's movement cost and the
    number of turns the route ends inside an enemy ZOC); a server that predates the walk sends four
    and the two read as ``-1``, "not known" - never as "clear".
    """
    est = PathingEstimate(turns=0, total_tiles=0, reachable_this_turn=0, waypoints=[])
    for line in lines:
        if line.startswith("PATH|"):
            parts = line.split("|")
            if len(parts) >= 4:
                est.turns = int(parts[1])
                est.total_tiles = int(parts[2])
                est.reachable_this_turn = int(parts[3])
            if len(parts) >= 6:
                est.total_cost = int(_number(parts[4]))
                est.zoc_stops = int(_number(parts[5]))
        elif line.startswith("ZOCSTOP|"):
            parts = line.split("|")
            if len(parts) >= 3:
                x, y = (int(v) for v in parts[1].split(","))
                est.zoc_at = (x, y, int(_number(parts[2])))
        elif line.startswith("WAYPOINTS|"):
            est.waypoints = line.split("|", 1)[1].split(";")
    return est


# The staging plan: the target city's ring, our units, and the game's own pathing for every
# (unit, ring tile) pair. Human instruction 2026-09-26: 在集结前，规划集结方案，不能被堵住，不同部队移动力不一样，找到最优集结方案后，才开始执行. Built as one query because the alternative is one
# `get_pathing_estimate` call per unit per ring tile, and the arithmetic that decides the plan
# (which tile, for which unit, in which turn) has to come from `UnitManager.GetMoveToPath` and
# `GetReachableMovement` —hand-computed hex distance was wrong twice this war.
_STAGING_TEMPLATE = """
local me = Game.GetLocalPlayer()
local tx, ty = __TX__, __TY__
local pTarget = Map.GetPlot(tx, ty)
if not pTarget then
    print("ERR:INVALID_TARGET|__TX__,__TY__")
    print("__SENTINEL__")
    return
end
__MARCH__
-- How far out the ring runs: the longest attack range any of our shooters has, so a gun that
-- outranges the city's two-tile strike is offered the tile it can actually fire from with no
-- answer (human instruction 2026-10-08: 远程部队攻击位置优先按射程最大来安排). Two is the floor -
-- every unpromoted shooter has it - and four is the cap this scan bothers with. The common case,
-- an army of range-2 guns, builds exactly the ring it built before.
local maxRange = 2
for _, u in Players[me]:GetUnits():Members() do
    if u:GetX() ~= -9999 then
        local ui = GameInfo.Units[u:GetType()]
        if ui and ((ui.RangedCombat or 0) > 0 or (ui.Bombard or 0) > 0) then
            local ur = ui.Range or 1
            if ur > maxRange then maxRange = ur end
        end
    end
end
if maxRange > 4 then maxRange = 4 end
local ring = {}
for dx = -maxRange, maxRange do for dy = -maxRange, maxRange do
    local px, py = tx + dx, ty + dy
    local p = Map.GetPlot(px, py)
    if p then
        local d = Map.GetPlotDistance(tx, ty, px, py)
        if d >= 1 and d <= maxRange then
            local passable = not p:IsImpassable()
            -- The map's own sight numbers, for the manual's line-of-sight rule (manual:999: "a
            -- unit cannot see a target if a blocking object is between the two units, such as a
            -- Mountain, Hill, or a Woods tile ... units on Hills can see over blocking terrain,
            -- unless the blocking terrain contains both Hills and Woods"). The rule is the
            -- manual's and the numbers are the game's: `SightThroughModifier` is 1 for Hills,
            -- Woods and Rainforest, 2 for Mountains and the tall Natural Wonders, and a
            -- Hills+Woods tile sums to 2 - which is exactly the manual's exception. The tool
            -- applies the rule; this query only reports the facts, because the engine's own
            -- answer exists for a unit standing on a tile and not for a tile it has not reached.
            local tinfo = GameInfo.Terrains[p:GetTerrainType()]
            local finfo = GameInfo.Features[p:GetFeatureType()]
            local hills = (tinfo and tinfo.Hills) and 1 or 0
            local sight = ((tinfo and tinfo.SightThroughModifier) or 0)
                + ((finfo and finfo.SightThroughModifier) or 0)
            ring[#ring + 1] = {x = px, y = py, d = d, idx = p:GetIndex(),
                passable = passable, water = p:IsWater(), hills = hills, sight = sight}
        end
    end
end end
-- One row per ring tile, and for every tile at distance 2 or more the tiles strictly between it
-- and the target, found with the game's own `Map.GetPlotDistance` rather than a hand-computed hex
-- offset (hand-computed hex has been wrong twice in this war): a tile `n` is between the shooter's
-- tile `t` and the target when `dist(t,n) + dist(n,target) == dist(t,target)`. For a distance-2
-- tile that reduces to exactly the distance-1 ring tiles adjacent to it, which is what this test
-- used to spell out. `-1` marks an intervening tile no shot crosses: impassable covers Mountains,
-- the Natural Wonders and Ice, which the manual calls impenetrable.
for _, t in ipairs(ring) do
    local via = ""
    if t.d >= 2 then
        local parts = {}
        for _, n in ipairs(ring) do
            if n.d >= 1 and n.d < t.d
                and (Map.GetPlotDistance(t.x, t.y, n.x, n.y) + n.d) == t.d then
                parts[#parts + 1] = n.x .. "," .. n.y .. "," .. (n.passable and n.sight or -1)
            end
        end
        via = "|via:" .. table.concat(parts, ";")
    end
    print("RING|" .. t.x .. "," .. t.y .. "|" .. t.d .. "|"
        .. (t.passable and "ok" or "impassable") .. "|"
        .. (t.water and "water" or "land")
        .. "|hill:" .. t.hills .. "|sight:" .. t.sight .. via)
end
-- A camp is a target of this same plan: the pre-war analysis, the staging before the assault and
-- the assault itself apply to every city AND every barbarian camp (human instruction 2026-09-26).
-- The ring, the paths and the assignments are identical; what differs is the last step - a camp has
-- no HP, no walls and no supply line, and one unit walking onto its tile destroys it. The flag is
-- read from the game rather than from the tile's improvement, so a camp somebody else already
-- cleared reads as a plain tile, and a city tile never reads as a camp. A failed call leaves the
-- flag false, which is the city wording - the safe default for a plan that fires from 2, the floor
-- every unpromoted shooter has.
local isCamp = false
pcall(function()
    isCamp = (Cities.GetCityInPlot(tx, ty) == nil)
end)
print("STAGEPLAN|" .. tx .. "," .. ty .. "|ring:" .. #ring .. "|camp:" .. (isCamp and "1" or "0"))
-- The next objective's ring, when the caller named one: surplus units advance toward it instead
-- of idling (human instruction 2026-09-26: 多余部队还可以向下一个城市目标/蛮族营地集结推进). The
-- march is what 007's clock was lost to, so the unit that will be needed there is moved now.
local nextRing = {}
local ntx, nty = __NX__, __NY__
if ntx ~= -9999 then
    for dx = -2, 2 do for dy = -2, 2 do
        local px, py = ntx + dx, nty + dy
        local p = Map.GetPlot(px, py)
        if p then
            local d = Map.GetPlotDistance(ntx, nty, px, py)
            if d >= 1 and d <= 2 and not p:IsImpassable() then
                nextRing[#nextRing + 1] = {x = px, y = py, d = d, idx = p:GetIndex()}
                print("NEXTRING|" .. px .. "," .. py .. "|" .. d)
            end
        end
    end end
end
-- A unit to eliminate, when the caller named one (in practice a missionary: human instruction
-- 2026-09-26: 多余部队里机动性高的部队还可以集火消灭传教士). The ring around it is what matters,
-- not the tile: a religious unit that is attacked dies, so the job is getting a military unit
-- ADJACENT to it (condemn is one command from there) and occupying its neighbours so it cannot
-- step away.
local killRing = {}
local ktx, kty = __KX__, __KY__
if ktx ~= -9999 then
    for dx = -1, 1 do for dy = -1, 1 do
        local px, py = ktx + dx, kty + dy
        local p = Map.GetPlot(px, py)
        if p and (dx ~= 0 or dy ~= 0) then
            if Map.GetPlotDistance(ktx, kty, px, py) == 1 then
                killRing[#killRing + 1] = {x = px, y = py, idx = p:GetIndex()}
                print("KILLRING|" .. px .. "," .. py)
            end
        end
    end end
end
-- The assembly ring: the tiles at distance 3, outside the city's two-tile strike. Human
-- instruction 2026-09-26 (plan the assembly before the first move) and the measured cost of
-- skipping it - 底比斯 opened with 2 of 3 shooters in position, 亚历山大 with 2 of 5, the rest
-- still walking. These are NOT firing tiles: nothing is assigned to them, they are where a unit
-- forms up before stepping onto the ring. Capped at the six nearest the army's centre of mass, so
-- the per-unit path scan stays the same order of magnitude as the ring's own.
local rallyRing = {}
do
    local sx, sy, n = 0, 0, 0
    for _, u in Players[me]:GetUnits():Members() do
        local ux, uy = u:GetX(), u:GetY()
        if ux ~= -9999 then
            local info = GameInfo.Units[u:GetType()]
            local cs = info and info.Combat or 0
            local rs = info and info.RangedCombat or 0
            local bomb = info and info.Bombard or 0
            if (cs + rs + bomb) > 0 then sx, sy, n = sx + ux, sy + uy, n + 1 end
        end
    end
    local cx, cy = tx, ty
    if n > 0 then cx, cy = math.floor(sx / n), math.floor(sy / n) end
    local candidates = {}
    for dx = -3, 3 do for dy = -3, 3 do
        local px, py = tx + dx, ty + dy
        local p = Map.GetPlot(px, py)
        if p and Map.GetPlotDistance(tx, ty, px, py) == 3 and not p:IsImpassable() then
            candidates[#candidates + 1] = {x = px, y = py, d = 3, idx = p:GetIndex(),
                away = Map.GetPlotDistance(cx, cy, px, py)}
        end
    end end
    table.sort(candidates, function(a, b) return a.away < b.away end)
    for i = 1, math.min(#candidates, 6) do
        local t = candidates[i]
        rallyRing[#rallyRing + 1] = t
        local p = Map.GetPlot(t.x, t.y)
        print("RALLYRING|" .. t.x .. "," .. t.y .. "|3|ok|"
            .. (p:IsWater() and "water" or "land"))
    end
end
for _, u in Players[me]:GetUnits():Members() do
    local ux, uy = u:GetX(), u:GetY()
    if ux ~= -9999 then
        local info = GameInfo.Units[u:GetType()]
        local cs = info and info.Combat or 0
        local rs = info and info.RangedCombat or 0
        local bomb = info and info.Bombard or 0
        if (cs + rs + bomb) > 0 then
            local moves = u:GetMovesRemaining()
            local reach = UnitManager.GetReachableMovement(u)
            local reachSet = {}
            if reach then for _, i in ipairs(reach) do reachSet[i] = true end end
            -- The walk's per-unit inputs, read once: the unit's own per-turn budget and whether it
            -- is a cavalry unit, which ignores ZOC (manual:735-737).
            local perTurnU = _marchPerTurn(u)
            local ignoreZocU = _marchIgnoresZoc(u)
            -- Recon is not a front-line unit: a Scout has Combat 10, so a test that only asks
            -- "is Combat > 0" files it as melee and the plan sends it to a tile adjacent to a
            -- city, where it dies for nothing. The unit that showed it was a Scout on the first
            -- live run of this query; the id it carried is not repeated here, because an id is
            -- one match's state and this file is not.
            local role = "melee"
            local ut = info and info.UnitType or "?"
            if string.find(ut, "SCOUT") or string.find(ut, "EXPLORER") then role = "recon"
            elseif bomb > 0 then role = "siege"
            elseif rs > 0 and (info.Range or 1) >= 2 then role = "ranged"
            elseif rs > 0 then role = "short-ranged" end
            print("UNIT|" .. ut .. "|" .. u:GetID() .. "|"
                .. ux .. "," .. uy .. "|" .. moves .. "|" .. role
                .. "|d" .. Map.GetPlotDistance(ux, uy, tx, ty) .. "|cs" .. cs
                .. "|hp" .. (u:GetMaxDamage() - u:GetDamage()) .. "/" .. u:GetMaxDamage()
                -- The unit's own range, so the plan ranks ring tiles against the range this gun
                -- actually has rather than a constant 2 (human instruction 2026-10-08).
                .. "|rg" .. (info and info.Range or 1))
            -- The engine's own answer for a gun that is **already** where it would fire from: the
            -- same `CanStartOperation(RANGE_ATTACK)` the attack path uses, aimed at the target
            -- tile. It is what turns the map's sight numbers above into a reading for a unit in
            -- position, and it is the oracle the map rule can be calibrated against tile by tile.
            -- A gun with no movement left is reported as `spent` rather than skipped: it is in the
            -- ring and it cannot shoot this turn, which is a different fact from "the map says the
            -- line is clear" - a unit that spends its move arriving fires NEXT turn.
            if (rs > 0 or bomb > 0) and Map.GetPlotDistance(ux, uy, tx, ty) <= (info and info.Range or 1) then
                if moves <= 0 then
                    print("CANFIRE|" .. u:GetID() .. "|0|spent")
                else
                    local lp = {{}}
                    lp[UnitOperationTypes.PARAM_X] = tx
                    lp[UnitOperationTypes.PARAM_Y] = ty
                    local okF, canF = pcall(function()
                        return UnitManager.CanStartOperation(u, UnitOperationTypes.RANGE_ATTACK, nil, lp)
                    end)
                    if okF then
                        print("CANFIRE|" .. u:GetID() .. "|" .. (canF and 1 or 0) .. "|ok")
                    end
                end
            end
            if ntx ~= -9999 and moves > 0 then
                for _, t2 in ipairs(nextRing) do
                    local path2 = UnitManager.GetMoveToPath(u, t2.idx)
                    if path2 and #path2 > 0 then
                        local last2 = Map.GetPlotByIndex(path2[#path2])
                        if last2:GetX() == t2.x and last2:GetY() == t2.y then
                            local rc2 = 0
                            for _, pIdx in ipairs(path2) do
                                if reachSet[pIdx] then rc2 = rc2 + 1 end
                            end
                            local turns2, cost2, zoc2, sx2, sy2, st2 =
                                _marchWalk(me, u, path2, reachSet, perTurnU, ignoreZocU)
                            if turns2 == nil then
                                cost2, zoc2 = -1, -1
                                if rc2 >= #path2 then turns2 = 0
                                else turns2 = math.ceil((#path2 - rc2) / math.max(rc2, 1)) end
                            end
                            if turns2 <= 3 then
                                print("NEXTOPTION|" .. u:GetID() .. "|" .. t2.x .. "," .. t2.y
                                    .. "|" .. turns2 .. "|" .. (reachSet[t2.idx] and 1 or 0)
                                    .. _marchTokens(cost2, zoc2, sx2, sy2, st2))
                            end
                        end
                    end
                end
            end
            if ktx ~= -9999 and moves > 0 then
                for _, t3 in ipairs(killRing) do
                    local path3 = UnitManager.GetMoveToPath(u, t3.idx)
                    if path3 and #path3 > 0 then
                        local last3 = Map.GetPlotByIndex(path3[#path3])
                        if last3:GetX() == t3.x and last3:GetY() == t3.y then
                            local rc3 = 0
                            for _, pIdx in ipairs(path3) do
                                if reachSet[pIdx] then rc3 = rc3 + 1 end
                            end
                            local turns3, cost3, zoc3, sx3, sy3, st3 =
                                _marchWalk(me, u, path3, reachSet, perTurnU, ignoreZocU)
                            if turns3 == nil then
                                cost3, zoc3 = -1, -1
                                if rc3 >= #path3 then turns3 = 0
                                else turns3 = math.ceil((#path3 - rc3) / math.max(rc3, 1)) end
                            end
                            if turns3 <= 3 then
                                print("KILLOPTION|" .. u:GetID() .. "|" .. t3.x .. "," .. t3.y
                                    .. "|" .. turns3 .. "|" .. (reachSet[t3.idx] and 1 or 0)
                                    .. _marchTokens(cost3, zoc3, sx3, sy3, st3))
                            end
                        end
                    end
                end
            end
            if moves > 0 then
                for _, t in ipairs(rallyRing) do
                    local path = UnitManager.GetMoveToPath(u, t.idx)
                    if path and #path > 0 then
                        local last = Map.GetPlotByIndex(path[#path])
                        if last:GetX() == t.x and last:GetY() == t.y then
                            local rc = 0
                            for _, pIdx in ipairs(path) do
                                if reachSet[pIdx] then rc = rc + 1 end
                            end
                            local turns, mcost, mzoc, msx, msy, mst =
                                _marchWalk(me, u, path, reachSet, perTurnU, ignoreZocU)
                            if turns == nil then
                                mcost, mzoc = -1, -1
                                if rc >= #path then turns = 0
                                else turns = math.ceil((#path - rc) / math.max(rc, 1)) end
                            end
                            if turns <= 3 then
                                print("RALLYOPTION|" .. u:GetID() .. "|" .. t.x .. "," .. t.y .. "|"
                                    .. turns .. "|" .. (reachSet[t.idx] and 1 or 0) .. "|" .. #path
                                    .. _marchTokens(mcost, mzoc, msx, msy, mst))
                            end
                        end
                    end
                end
            end
            if moves > 0 then
                for _, t in ipairs(ring) do
                    local path = UnitManager.GetMoveToPath(u, t.idx)
                    if path and #path > 0 then
                        local last = Map.GetPlotByIndex(path[#path])
                        if last:GetX() == t.x and last:GetY() == t.y then
                            local reachCount = 0
                            for _, pIdx in ipairs(path) do
                                if reachSet[pIdx] then reachCount = reachCount + 1 end
                            end
                            local turns, mcost, mzoc, msx, msy, mst =
                                _marchWalk(me, u, path, reachSet, perTurnU, ignoreZocU)
                            if turns == nil then
                                mcost, mzoc = -1, -1
                                if reachCount >= #path then turns = 0
                                else turns = math.ceil((#path - reachCount) / math.max(reachCount, 1)) end
                            end
                            if turns <= 3 then
                                print("OPTION|" .. u:GetID() .. "|" .. t.x .. "," .. t.y .. "|"
                                    .. turns .. "|" .. (reachSet[t.idx] and 1 or 0) .. "|" .. #path
                                    .. _marchTokens(mcost, mzoc, msx, msy, mst))
                            end
                        end
                    end
                end
            end
        end
    end
end
print("__SENTINEL__")
"""


def _number(text: str, default: float = 0) -> float:
    """A number the game printed: an int when it is whole, a float when it is not.

    The staging query prints movement straight from the game, and a unit can be
    holding a fraction of a point. Measured 2026-09-27: `get_staging_plan` died on
    `invalid literal for int() with base 10: '1.5'` while a Line Infantry stood at
    1.5/3, which cost the Alexandria assault the one table it needed most. Whole
    values keep their int shape, so nothing downstream changes for the normal case.
    """
    try:
        value = float(text)
    except (TypeError, ValueError):
        return default
    return int(value) if value.is_integer() else value


def build_staging_plan_query(
    target_x: int,
    target_y: int,
    next_x: int | None = None,
    next_y: int | None = None,
    kill_x: int | None = None,
    kill_y: int | None = None,
) -> str:
    """GameCore/InGame: the ring around a target city and every unit's path to each ring tile.

    One query instead of one per (unit, tile): the ring is at most ~18 tiles and the army is
    ~10 units, so the per-call version is a hundred round trips. Every number here comes from
    the game's own pathfinding (``GetMoveToPath`` + ``GetReachableMovement``) plus the walk in
    `_MARCH_HELPER`, which pays each tile's real movement cost and ends a turn where the route
    enters an enemy zone of control - that is the point: the staging plan decides *which tile for
    which unit in which turn*, and this war paid twice for computing that by hand.
    """
    return (
        _STAGING_TEMPLATE.replace("__TX__", str(int(_number(target_x))))
        .replace("__TY__", str(int(_number(target_y))))
        .replace("__MARCH__", _MARCH_HELPER)
        .replace(
            "__NX__", str(int(_number(next_x)) if next_x is not None else -9999)
        )
        .replace(
            "__NY__", str(int(_number(next_y)) if next_y is not None else -9999)
        )
        .replace(
            "__KX__", str(int(_number(kill_x)) if kill_x is not None else -9999)
        )
        .replace(
            "__KY__", str(int(_number(kill_y)) if kill_y is not None else -9999)
        )
        .replace("__SENTINEL__", SENTINEL)
    )


def _route_tokens(tokens: list[str]) -> tuple[int, int, tuple[int, int, int] | None]:
    """``zoc:`` / ``cost:`` / ``zocat:`` from an option line, when the server sends them.

    ``-1`` on either number means the server did not report it, and that is never the same as
    "clear": a plan built from an old server must not read an unknown route as a safe one.
    """
    cost, zoc, zoc_at = -1, -1, None
    for token in tokens:
        if token.startswith("zocat:"):
            bits = token[6:].split(",")
            if len(bits) == 3:
                zoc_at = (
                    int(_number(bits[0])),
                    int(_number(bits[1])),
                    int(_number(bits[2])),
                )
        elif token.startswith("zoc:"):
            zoc = int(_number(token[4:]))
        elif token.startswith("cost:"):
            cost = int(_number(token[5:]))
    return cost, zoc, zoc_at


def parse_staging_plan_response(lines: list[str]) -> StagingPlan:
    """``RING|``, ``UNIT|`` and ``OPTION|`` lines into a StagingPlan."""
    plan = StagingPlan()
    for line in lines:
        parts = line.split("|")
        if line.startswith("STAGEPLAN|") and len(parts) >= 3:
            plan.target = parts[1]
            # `camp:1` is printed by the current server; an older one printed neither token, and the
            # city wording is the safe default for a plan that fires from 2, the floor.
            plan.camp = any(token == "camp:1" for token in parts[2:])
        elif line.startswith("RING|") and len(parts) >= 5:
            x, y = (int(v) for v in parts[1].split(","))
            # The last three tokens are the map's sight facts and are optional: a server that
            # predates them sends five fields, and "not reported" must never read as "clear".
            hills = False
            sight = 0
            between: list[tuple[int, int, int]] = []
            for token in parts[5:]:
                if token.startswith("hill:"):
                    hills = token[5:] == "1"
                elif token.startswith("sight:"):
                    sight = int(_number(token[6:]))
                elif token.startswith("via:"):
                    for entry in token[4:].split(";"):
                        if not entry:
                            continue
                        vx, vy, level = entry.split(",")
                        between.append((int(vx), int(vy), int(_number(level))))
            plan.ring.append(
                StagingRingTile(
                    x=x,
                    y=y,
                    distance=int(_number(parts[2])),
                    blocked=parts[3] != "ok",
                    water=parts[4] == "water",
                    hills=hills,
                    sight=sight,
                    between=between,
                )
            )
        elif line.startswith("CANFIRE|") and len(parts) >= 3:
            unit_id = int(parts[1])
            plan.engine_fire[unit_id] = parts[2] == "1"
            # `spent` is not a line-of-sight verdict: the gun is in the ring and cannot shoot this
            # turn (no movement left), which is the one fact the map cannot show.
            if len(parts) > 3 and parts[3] == "spent":
                plan.engine_spent.add(unit_id)
        elif line.startswith("UNIT|") and len(parts) >= 6:
            x, y = (int(v) for v in parts[3].split(","))
            distance = strength = 0
            hp = max_hp = 0
            # The floor, for a line that does not carry `rg`: the plan then behaves exactly as it
            # did before per-unit ranges existed.
            unit_range = 2
            for token in parts[6:]:
                if token.startswith("d"):
                    distance = int(_number(token[1:]))
                elif token.startswith("cs"):
                    strength = int(_number(token[2:]))
                elif token.startswith("rg"):
                    unit_range = int(_number(token[2:]))
                elif token.startswith("hp") and "/" in token:
                    cur, _, total = token[2:].partition("/")
                    hp, max_hp = int(_number(cur)), int(_number(total))
            plan.units.append(
                StagingUnit(
                    unit_type=parts[1],
                    unit_id=int(parts[2]),
                    x=x,
                    y=y,
                    # Fractional on purpose: the game reports 1.5 of 3 moves.
                    moves=_number(parts[4]),
                    role=parts[5],
                    distance=distance,
                    strength=strength,
                    hp=hp,
                    max_hp=max_hp,
                    range=unit_range,
                )
            )
        elif line.startswith("RALLYRING|") and len(parts) >= 5:
            x, y = (int(v) for v in parts[1].split(","))
            plan.rally_ring.append(
                StagingRingTile(
                    x=x,
                    y=y,
                    distance=int(_number(parts[2])),
                    blocked=parts[3] != "ok",
                    water=parts[4] == "water",
                )
            )
        elif line.startswith("RALLYOPTION|") and len(parts) >= 6:
            x, y = (int(v) for v in parts[2].split(","))
            cost, zoc, zoc_at = _route_tokens(parts[6:])
            plan.rally_options.append(
                StagingOption(
                    unit_id=int(parts[1]),
                    x=x,
                    y=y,
                    turns=int(_number(parts[3])),
                    this_turn=parts[4] == "1",
                    path_len=int(_number(parts[5])),
                    cost=cost,
                    zoc=zoc,
                    zoc_at=zoc_at,
                )
            )
        elif line.startswith("KILLRING|") and len(parts) >= 2:
            x, y = (int(v) for v in parts[1].split(","))
            plan.kill_ring.append(StagingRingTile(x=x, y=y, distance=1))
        elif line.startswith("KILLOPTION|") and len(parts) >= 5:
            x, y = (int(v) for v in parts[2].split(","))
            cost, zoc, zoc_at = _route_tokens(parts[5:])
            plan.kill_options.append(
                StagingOption(
                    unit_id=int(parts[1]),
                    x=x,
                    y=y,
                    turns=int(_number(parts[3])),
                    this_turn=parts[4] == "1",
                    cost=cost,
                    zoc=zoc,
                    zoc_at=zoc_at,
                )
            )
        elif line.startswith("NEXTRING|") and len(parts) >= 3:
            x, y = (int(v) for v in parts[1].split(","))
            plan.next_ring.append(
                StagingRingTile(x=x, y=y, distance=int(_number(parts[2])))
            )
        elif line.startswith("NEXTOPTION|") and len(parts) >= 5:
            x, y = (int(v) for v in parts[2].split(","))
            cost, zoc, zoc_at = _route_tokens(parts[5:])
            plan.next_options.append(
                StagingOption(
                    unit_id=int(parts[1]),
                    x=x,
                    y=y,
                    turns=int(_number(parts[3])),
                    this_turn=parts[4] == "1",
                    cost=cost,
                    zoc=zoc,
                    zoc_at=zoc_at,
                )
            )
        elif line.startswith("OPTION|") and len(parts) >= 6:
            x, y = (int(v) for v in parts[2].split(","))
            cost, zoc, zoc_at = _route_tokens(parts[6:])
            plan.options.append(
                StagingOption(
                    unit_id=int(parts[1]),
                    x=x,
                    y=y,
                    turns=int(_number(parts[3])),
                    this_turn=parts[4] == "1",
                    path_len=int(_number(parts[5])),
                    cost=cost,
                    zoc=zoc,
                    zoc_at=zoc_at,
                )
            )
    return plan


# ---------------------------------------- Post-move visibility ----------------------------------------


def build_reinforcement_query(target_x: int, target_y: int) -> str:
    """InGame: military units under construction, and how far each is from the target.

    `tactics/07` step 3's question - "how long, and what will it cost" - has a leg nothing joined:
    the queue says when a unit appears (`bq:GetTurnsLeft()`, the same count `get_cities` prints) and
    the map says how far away it is, and the two live in different tools. This reads both in one
    pass, per city, for **military** units only (`Combat`/`RangedCombat`/`Bombard` > 0) - a Granary
    is not a reinforcement.

    The march leg is a hex distance at the unit's own `BaseMoves`, and it is deliberately an
    estimate: the game's pathfinding (`UnitManager.GetMoveToPath`) takes a unit, and the unit being
    built does not exist yet. The turn it appears, `get_staging_plan` answers the same question
    exactly, with terrain costs and the reachable set.
    """
    return f"""
local me = Game.GetLocalPlayer()
local tx, ty = {target_x}, {target_y}
local hashName = {{}}
for u in GameInfo.Units() do hashName[u.Hash] = u.UnitType end
for b in GameInfo.Buildings() do hashName[b.Hash] = b.BuildingType end
for d in GameInfo.Districts() do hashName[d.Hash] = d.DistrictType end
for p in GameInfo.Projects() do hashName[p.Hash] = p.ProjectType end
-- The assembly ring: the passable distance-3 tiles, which is where the doctrine forms up (outside
-- a city's two-tile strike). The nearest one to the building city is the rally this unit walks to.
local ring = {{}}
for dx = -3, 3 do for dy = -3, 3 do
    local px, py = tx + dx, ty + dy
    local p = Map.GetPlot(px, py)
    if p and Map.GetPlotDistance(tx, ty, px, py) == 3 and not p:IsImpassable() then
        ring[#ring + 1] = {{x = px, y = py}}
    end
end end
for _, c in Players[me]:GetCities():Members() do
    local bq = c:GetBuildQueue()
    if bq and bq:GetSize() > 0 then
        local h = bq:GetCurrentProductionTypeHash()
        local name = hashName[h] or ""
        if string.find(name, "^UNIT_") then
            local info = GameInfo.Units[name]
            local cs = info and info.Combat or 0
            local rs = info and info.RangedCombat or 0
            local bomb = info and info.Bombard or 0
            if (cs + rs + bomb) > 0 then
                -- The same role rule the staging plan uses, so "one siege in place, one siege
                -- building" is a comparison of like with like.
                local role = "melee"
                if string.find(name, "SCOUT") or string.find(name, "EXPLORER") then role = "recon"
                elseif bomb > 0 then role = "siege"
                elseif rs > 0 and (info.Range or 1) >= 2 then role = "ranged"
                elseif rs > 0 then role = "short-ranged" end
                local cx, cy = c:GetX(), c:GetY()
                local best, bestD = nil, 999
                for _, t in ipairs(ring) do
                    local d = Map.GetPlotDistance(cx, cy, t.x, t.y)
                    if d < bestD then best, bestD = t, d end
                end
                local cName = "unknown"
                pcall(function() cName = Locale.Lookup(c:GetName()):gsub("|", "/") end)
                print("REINF|" .. name .. "|" .. role
                    .. "|moves:" .. (info and info.BaseMoves or 2)
                    .. "|ready:" .. bq:GetTurnsLeft()
                    .. "|dist:" .. Map.GetPlotDistance(cx, cy, tx, ty)
                    .. "|rally:" .. (best and (best.x .. "," .. best.y) or "-")
                    .. "|rallydist:" .. (best and bestD or -1)
                    .. "|city:" .. cName .. "|cityxy:" .. cx .. "," .. cy)
            end
        end
    end
end
print("{SENTINEL}")
""".replace("{SENTINEL}", SENTINEL)


def parse_reinforcement_response(lines: list[str]) -> list[Reinforcement]:
    """Parse `REINF|` rows into `Reinforcement` records."""
    out: list[Reinforcement] = []
    for line in lines:
        parts = line.split("|")
        if not line.startswith("REINF|") or len(parts) < 3:
            continue
        fields: dict[str, str] = {}
        for token in parts[3:]:
            key, _, value = token.partition(":")
            fields[key] = value
        rally: tuple[int, int] | None = None
        if fields.get("rally", "-") not in ("", "-"):
            rx, ry = fields["rally"].split(",")
            rally = (int(rx), int(ry))
        city_x = city_y = 0
        if fields.get("cityxy", ""):
            cx, cy = fields["cityxy"].split(",")
            city_x, city_y = int(cx), int(cy)
        out.append(
            Reinforcement(
                unit_type=parts[1],
                role=parts[2],
                moves=int(_number(fields.get("moves", "2"))),
                ready_turns=int(_number(fields.get("ready", "0"))),
                distance=int(_number(fields.get("dist", "0"))),
                rally=rally,
                rally_distance=int(_number(fields.get("rallydist", "0"))),
                city=fields.get("city", ""),
                city_x=city_x,
                city_y=city_y,
            )
        )
    return out


def build_post_move_visibility_query(now_x: int, now_y: int, radius: int = 4) -> str:
    """GameCore: scan tiles around a position and return revealed tile data.

    Used after a unit move to compute newly-revealed tiles via Python-side diff.
    Radius 4 covers all standard sight ranges (2 for most units, 3 for scouts).
    Output: ``TILE|x,y|terrain|feature|resource:class|hills|camp|units|city``
    """
    return f"""
local cx, cy, r = {now_x}, {now_y}, {radius}
local me = Game.GetLocalPlayer()
local vis = PlayersVisibility[me]
local pTech = Players[me]:GetTechs()
{_LUA_RES_VISIBLE}
for dy = -r, r do
    for dx = -r, r do
        local x, y = cx + dx, cy + dy
        local plot = Map.GetPlot(x, y)
        if plot and vis:IsRevealed(plot:GetX(), plot:GetY()) then
            local terrain = GameInfo.Terrains[plot:GetTerrainType()].TerrainType
            local feature = "none"
            local fi = plot:GetFeatureType()
            if fi >= 0 then feature = GameInfo.Features[fi].FeatureType end
            local resource = "none"
            local ri = plot:GetResourceType()
            if ri >= 0 then
                local re = GameInfo.Resources[ri]
                if resVisible(re) then
                    resource = re.ResourceType .. ":" .. (re.ResourceClassType or "")
                end
            end
            local hills = plot:IsHills() and "1" or "0"
            local camp = "0"
            local ii = plot:GetImprovementType()
            if ii >= 0 then
                local iInfo = GameInfo.Improvements[ii]
                if iInfo and iInfo.ImprovementType == "IMPROVEMENT_BARBARIAN_CAMP" then
                    camp = "1"
                end
            end
            local units = "none"
            if vis:IsVisible(plot:GetX(), plot:GetY()) then
                local uParts = {{}}
                for pid = 0, 63 do
                    if pid ~= me and Players[pid] and Players[pid]:IsAlive() then
                        for _, u in Players[pid]:GetUnits():Members() do
                            if u:GetX() == x and u:GetY() == y then
                                local entry = GameInfo.Units[u:GetType()]
                                local nm = entry and entry.UnitType or "UNKNOWN"
                                local ownerLabel = "Barbarian"
                                if pid ~= 63 then
                                    local cfg = PlayerConfigurations[pid]
                                    if cfg then ownerLabel = Locale.Lookup(cfg:GetCivilizationShortDescription()) end
                                end
                                table.insert(uParts, ownerLabel .. " " .. nm:gsub("UNIT_", ""))
                            end
                        end
                    end
                end
                if #uParts > 0 then units = table.concat(uParts, ";") end
            end
            local cityName = "none"
            local cityOwner = "none"
            if plot:IsCity() then
                local cOwner = plot:GetOwner()
                if cOwner >= 0 and cOwner ~= me then
                    if cOwner == 63 then cityOwner = "Barbarian"
                    else
                        local cfg2 = PlayerConfigurations[cOwner]
                        if cfg2 then cityOwner = Locale.Lookup(cfg2:GetCivilizationShortDescription()) end
                    end
                    pcall(function()
                        for _, c in Players[cOwner]:GetCities():Members() do
                            if c:GetX() == x and c:GetY() == y then
                                cityName = Locale.Lookup(c:GetName())
                                break
                            end
                        end
                    end)
                end
            end
            -- `visible` is the difference between "in sight right now" and "known from an earlier
            -- look": the row is printed for every *revealed* plot, so a caller that wants to say
            -- what a unit can see this turn has to ask, and a city remembered from ten turns ago
            -- must not be reported as newly seen.
            local visible = vis:IsVisible(plot:GetX(), plot:GetY()) and "1" or "0"
            print("TILE|" .. x .. "," .. y .. "|" .. terrain .. "|" .. feature .. "|" .. resource .. "|" .. hills .. "|" .. camp .. "|" .. units .. "|" .. cityName .. "|" .. cityOwner .. "|" .. visible)
        end
    end
end
print("{SENTINEL}")
"""


def parse_post_move_visibility(
    lines: list[str],
) -> list[tuple[int, int, dict]]:
    """Parse TILE| lines from post-move visibility query.

    Returns (x, y, metadata) tuples where metadata contains terrain, feature,
    resource, resource_class, hills, camp, units, city, city_owner and visible.

    The last two fields are optional: a server that predates them sends nine, and "not reported"
    reads as ``city_owner=None`` / ``visible=True`` (the old behaviour, where every row of the scan
    was treated as something the unit could see).
    """
    results: list[tuple[int, int, dict]] = []
    for line in lines:
        if not line.startswith("TILE|"):
            continue
        parts = line.split("|")
        if len(parts) < 9:
            continue
        xy = parts[1].split(",")
        x, y = int(xy[0]), int(xy[1])
        # Parse resource into name + class
        resource = None
        resource_class = None
        if parts[4] != "none":
            rp = parts[4].split(":", 1)
            resource = rp[0]
            if len(rp) > 1 and rp[1]:
                resource_class = rp[1].replace("RESOURCECLASS_", "").lower()
        meta = {
            "terrain": parts[2],
            "feature": None if parts[3] == "none" else parts[3],
            "resource": resource,
            "resource_class": resource_class,
            "hills": parts[5] == "1",
            "camp": parts[6] == "1",
            "units": None if parts[7] == "none" else parts[7].split(";"),
            "city": None if parts[8] == "none" else parts[8],
            "city_owner": None if len(parts) <= 9 or parts[9] == "none" else parts[9],
            "visible": True if len(parts) <= 10 else parts[10] == "1",
        }
        results.append((x, y, meta))
    return results


def build_builder_tasks_query() -> str:
    """InGame context: scans all owned tiles for improvement tasks and all idle builders.

    Outputs TASK| lines for tiles needing work and BUILDER| lines for builder units.
    Uses hardcoded resource mapping and terrain heuristics for improvement recommendations.
    Does NOT use CanStartOperation with remote tiles (corrupts engine state —crash).
    """
    return """
local me = Game.GetLocalPlayer()
local pTech = Players[me]:GetTechs()
-- A strategic resource the player has not unlocked yet is still returned by
-- `Plot:GetResourceType()`, and this scan used to emit an URGENT task for it - measured live T60,
-- where 北京's row carried an unimproved NITER at (58,30), a Builder was sent there, and the MINE
-- was refused ("tile has FEATURE_FLOODPLAINS_GRASSLAND ... can build here: IMPROVEMENT_FARM")
-- because Niter needs Gunpowder, a Renaissance tech: the tile's resource was invisible to the map
-- query the whole time. An unbuildable URGENT task is worse than no task, because it moves a
-- Builder. Same predicate the map/settle queries use (`_helpers.resVisible`).
local function resVisible(resEntry)
    if not resEntry.PrereqTech then return true end
    local t = GameInfo.Technologies[resEntry.PrereqTech]
    return t and pTech:HasTech(t.Index)
end
local pCities = Players[me]:GetCities()

-- Gather all builders with charges
local builders = {}
for _, u in Players[me]:GetUnits():Members() do
    local entry = GameInfo.Units[u:GetType()]
    if entry and entry.UnitType == "UNIT_BUILDER" and u:GetBuildCharges() > 0 then
        local bx, by = u:GetX(), u:GetY()
        if bx ~= -9999 then
            table.insert(builders, {id=u:GetID(), idx=u:GetID() % 65536, x=bx, y=by, charges=u:GetBuildCharges(), moves=u:GetMovesRemaining()})
        end
    end
end

-- Hardcoded resource -> improvement mapping (avoids GameInfo.Improvement_ValidResources()
-- iterator which can crash the game engine with EXCEPTION_ACCESS_VIOLATION)
local resImpMap = {
    -- Strategic
    RESOURCE_HORSES="IMPROVEMENT_PASTURE", RESOURCE_IRON="IMPROVEMENT_MINE",
    RESOURCE_NITER="IMPROVEMENT_MINE", RESOURCE_COAL="IMPROVEMENT_MINE",
    RESOURCE_ALUMINUM="IMPROVEMENT_MINE", RESOURCE_URANIUM="IMPROVEMENT_MINE",
    RESOURCE_OIL="IMPROVEMENT_OIL_WELL",
    -- Luxury (mined/quarried)
    RESOURCE_DIAMONDS="IMPROVEMENT_MINE", RESOURCE_JADE="IMPROVEMENT_MINE",
    RESOURCE_MERCURY="IMPROVEMENT_MINE", RESOURCE_SALT="IMPROVEMENT_MINE",
    RESOURCE_SILVER="IMPROVEMENT_MINE", RESOURCE_AMBER="IMPROVEMENT_MINE",
    RESOURCE_GYPSUM="IMPROVEMENT_QUARRY", RESOURCE_MARBLE="IMPROVEMENT_QUARRY",
    -- Luxury (plantation)
    RESOURCE_CITRUS="IMPROVEMENT_PLANTATION", RESOURCE_COCOA="IMPROVEMENT_PLANTATION",
    RESOURCE_COFFEE="IMPROVEMENT_PLANTATION", RESOURCE_COTTON="IMPROVEMENT_PLANTATION",
    RESOURCE_DYES="IMPROVEMENT_PLANTATION", RESOURCE_INCENSE="IMPROVEMENT_PLANTATION",
    RESOURCE_OLIVES="IMPROVEMENT_PLANTATION", RESOURCE_SILK="IMPROVEMENT_PLANTATION",
    RESOURCE_SPICES="IMPROVEMENT_PLANTATION", RESOURCE_SUGAR="IMPROVEMENT_PLANTATION",
    RESOURCE_TEA="IMPROVEMENT_PLANTATION", RESOURCE_TOBACCO="IMPROVEMENT_PLANTATION",
    RESOURCE_WINE="IMPROVEMENT_PLANTATION",
    -- Luxury (camp)
    RESOURCE_FURS="IMPROVEMENT_CAMP", RESOURCE_IVORY="IMPROVEMENT_CAMP",
    RESOURCE_TRUFFLES="IMPROVEMENT_CAMP", RESOURCE_HONEY="IMPROVEMENT_CAMP",
    -- Bonus
    RESOURCE_BANANAS="IMPROVEMENT_PLANTATION", RESOURCE_CATTLE="IMPROVEMENT_PASTURE",
    RESOURCE_SHEEP="IMPROVEMENT_PASTURE", RESOURCE_DEER="IMPROVEMENT_CAMP",
    RESOURCE_COPPER="IMPROVEMENT_MINE", RESOURCE_STONE="IMPROVEMENT_QUARRY",
    RESOURCE_MAIZE="IMPROVEMENT_FARM", RESOURCE_RICE="IMPROVEMENT_FARM",
    RESOURCE_WHEAT="IMPROVEMENT_FARM",
    -- Water (builders can't reach, but listed for completeness)
    RESOURCE_FISH="IMPROVEMENT_FISHING_BOATS", RESOURCE_CRABS="IMPROVEMENT_FISHING_BOATS",
    RESOURCE_PEARLS="IMPROVEMENT_FISHING_BOATS", RESOURCE_TURTLES="IMPROVEMENT_FISHING_BOATS",
    RESOURCE_WHALES="IMPROVEMENT_FISHING_BOATS",
}

-- Scan city territory for tasks
local seen = {}
local normalCount = 0
local maxNormal = 20
for _, city in pCities:Members() do
    local cx, cy = city:GetX(), city:GetY()
    local cityName = Locale.Lookup(city:GetName())
    for dy = -3, 3 do for dx = -3, 3 do
        local px, py = cx + dx, cy + dy
        local key = px .. "," .. py
        if not seen[key] then
            seen[key] = true
            local plot = Map.GetPlot(px, py)
            if plot and plot:GetOwner() == me and not plot:IsWater() and not plot:IsMountain() then
                local distIdx = plot:GetDistrictType()
                local impIdx = plot:GetImprovementType()
                local resIdx = plot:GetResourceType()

                -- Skip tiles with districts
                if distIdx < 0 then
                    -- Check for pillaged improvements
                    if impIdx >= 0 then
                        local okP, pil = pcall(function() return plot:IsImprovementPillaged() end)
                        if okP and pil then
                            local impInfo = GameInfo.Improvements[impIdx]
                            local impName = impInfo and impInfo.ImprovementType or "UNKNOWN"
                            -- Find the nearest builder THAT CAN ACT. Measured T434: 3 of 4 `improve`
                            -- orders died with CANNOT_IMPROVE|Builder has no moves remaining this turn
                            -- because this pick looked at distance alone, and the nearest builder had
                            -- already spent its movement. One that cannot start the job this turn is
                            -- only the fallback, so the row still names somebody.
                            local nearId, nearDist = -1, 999
                            local fallbackId, fallbackDist = -1, 999
                            for _, b in ipairs(builders) do
                                local d = Map.GetPlotDistance(b.x, b.y, px, py)
                                if (b.moves or 0) > 0 then
                                    if d < nearDist then nearDist = d; nearId = b.id end
                                elseif d < fallbackDist then fallbackDist = d; fallbackId = b.id end
                            end
                            if nearId == -1 then nearId, nearDist = fallbackId, fallbackDist end
                            print("TASK|urgent|" .. px .. "," .. py .. "|REPAIR|" .. impName:gsub("IMPROVEMENT_", "") .. "|pillaged|" .. cityName .. "|" .. nearId .. "|" .. nearDist)
                        end
                    -- Check for unimproved resource tiles
                    elseif resIdx >= 0 and impIdx < 0 then
                        local resInfo = GameInfo.Resources[resIdx]
                        if resInfo and resVisible(resInfo) then
                            local resClass = resInfo.ResourceClassType or ""
                            local resName = resInfo.ResourceType:gsub("RESOURCE_", "")
                            local priority = "normal"
                            if resClass == "RESOURCECLASS_STRATEGIC" then priority = "urgent"
                            elseif resClass == "RESOURCECLASS_LUXURY" then priority = "high"
                            elseif resClass == "RESOURCECLASS_BONUS" then priority = "high"
                            end
                            -- Find valid improvement via resource lookup table
                            local validImp = resImpMap[resInfo.ResourceType]
                            if validImp then
                                -- Check tech prerequisite
                                local impInfo = GameInfo.Improvements[validImp]
                                if impInfo and impInfo.PrereqTech then
                                    local techInfo = GameInfo.Technologies[impInfo.PrereqTech]
                                    if techInfo and not Players[me]:GetTechs():HasTech(techInfo.Index) then
                                        validImp = validImp .. "_LOCKED"
                                    end
                                end
                                -- Find nearest builder
                                local nearId, nearDist = -1, 999
                                for _, b in ipairs(builders) do
                                    local d = Map.GetPlotDistance(b.x, b.y, px, py)
                                    if d < nearDist then nearDist = d; nearId = b.id end
                                end
                                local classShort = "bonus"
                                if resClass == "RESOURCECLASS_STRATEGIC" then classShort = "strategic"
                                elseif resClass == "RESOURCECLASS_LUXURY" then classShort = "luxury"
                                end
                                print("TASK|" .. priority .. "|" .. px .. "," .. py .. "|" .. validImp .. "|" .. resName .. "|" .. classShort .. "|" .. cityName .. "|" .. nearId .. "|" .. nearDist)
                            end
                            -- A resource with no mapped improvement is not builder work. The antiquity
                            -- sites are the case that shows up - they are resources with no `resImpMap`
                            -- entry, and an Archaeologist digs them, not a builder. Printing `build
                            -- UNKNOWN` for one read as a job, which is how a builder ends up parked on a
                            -- tile it cannot touch: measured 2026-10-04, T354, builder 13107256 stood on
                            -- an antiquity site at (36,22) flagged `[cannot act]`, in no work list at all.
                        end
                    -- Check for empty tiles that could use standard improvements (capped)
                    -- Uses terrain heuristics instead of CanStartOperation (which corrupts
                    -- engine state when called with remote tile coordinates, causing
                    -- EXCEPTION_ACCESS_VIOLATION during end_turn)
                    elseif impIdx < 0 and resIdx < 0 and normalCount < maxNormal then
                        local featureIdx = plot:GetFeatureType()
                        local terrIdx = plot:GetTerrainType()
                        local terrInfo = terrIdx >= 0 and GameInfo.Terrains[terrIdx] or nil
                        local terrName = terrInfo and terrInfo.TerrainType or ""
                        local bestImp = nil
                        -- The feature decides before the terrain does. Checking `IsHills()` first
                        -- recommended `IMPROVEMENT_MINE` for a FORESTED hill, which the engine
                        -- refuses: measured T353-T361 at (61,35), a `build MINE` task that stood for
                        -- eight turns while a builder walked seven tiles to it, answered twice with
                        -- `CANNOT_IMPROVE|... tile has FEATURE_FOREST (use remove_feature first).
                        -- can build here: IMPROVEMENT_LUMBER_MILL`. A Lumber Mill needs no feature
                        -- removal, so it is the improvement for the tile as it stands - and it is
                        -- what the builder ended up building both times.
                        if featureIdx >= 0 then
                            local fInfo = GameInfo.Features[featureIdx]
                            local fName = fInfo and fInfo.FeatureType or ""
                            if fName == "FEATURE_FOREST" then
                                bestImp = "IMPROVEMENT_LUMBER_MILL"
                            end
                            -- Jungle/marsh need removal first, skip
                        elseif plot:IsHills() then
                            bestImp = "IMPROVEMENT_MINE"
                        elseif terrName == "TERRAIN_DESERT" or terrName == "TERRAIN_SNOW" or terrName == "TERRAIN_TUNDRA" then
                            -- Low-yield terrain, skip
                        else
                            bestImp = "IMPROVEMENT_FARM"
                        end
                        if bestImp then
                            local nearId, nearDist = -1, 999
                            for _, b in ipairs(builders) do
                                local d = Map.GetPlotDistance(b.x, b.y, px, py)
                                if d < nearDist then nearDist = d; nearId = b.id end
                            end
                            print("TASK|normal|" .. px .. "," .. py .. "|" .. bestImp .. "||none|" .. cityName .. "|" .. nearId .. "|" .. nearDist)
                            normalCount = normalCount + 1
                        end
                    end
                end
            end
        end
    end end
end

-- Print builder info
for _, b in ipairs(builders) do
    print("BUILDER|" .. b.id .. "|" .. b.idx .. "|" .. b.x .. "," .. b.y .. "|" .. b.charges .. "|" .. string.format("%.1f", b.moves))
end
print("{SENTINEL}")
""".replace("{SENTINEL}", SENTINEL)


def parse_builder_tasks(
    lines: list[str],
) -> tuple[list[BuilderTask], list[BuilderInfo]]:
    """Parse TASK| and BUILDER| lines from build_builder_tasks_query."""
    tasks: list[BuilderTask] = []
    builders: list[BuilderInfo] = []

    for line in lines:
        try:
            if line.startswith("TASK|"):
                parts = line.split("|")
                if len(parts) < 9:
                    continue
                xy = parts[2].split(",")
                if len(xy) != 2:
                    continue
                imp = parts[3]
                # Skip tasks where tech prerequisite isn't met
                if imp.endswith("_LOCKED"):
                    continue
                tasks.append(
                    BuilderTask(
                        priority=parts[1],
                        x=int(xy[0]),
                        y=int(xy[1]),
                        improvement=imp,
                        resource=parts[4],
                        resource_class=parts[5],
                        city_name=parts[6],
                        nearest_builder_id=int(parts[7]),
                        distance=int(parts[8]),
                    )
                )
            elif line.startswith("BUILDER|"):
                parts = line.split("|")
                if len(parts) < 6:
                    continue
                xy = parts[3].split(",")
                if len(xy) != 2:
                    continue
                builders.append(
                    BuilderInfo(
                        unit_id=int(parts[1]),
                        unit_index=int(parts[2]),
                        x=int(xy[0]),
                        y=int(xy[1]),
                        charges=int(parts[4]),
                        moves=float(parts[5]),
                    )
                )
        except (ValueError, IndexError):
            continue

    return tasks, builders
