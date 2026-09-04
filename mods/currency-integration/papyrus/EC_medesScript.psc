;/ Decompiled by Champollion V1.0.1
Source   : EC_medesScript.psc
Modified : 2026-05-20 20:57:00
Compiled : 2026-05-20 20:57:25
User     : victo
Computer : LAPTOP-5P8G2UR1
/;
scriptName EC_medesScript extends EC_altCurrencyFunctions

;-- Properties --------------------------------------
miscobject property Mede auto
perk property medePerk auto

;-- Variables ---------------------------------------
Bool inMede

;-- Functions ---------------------------------------

function OnLocationChange(location akOldLoc, location akNewLoc)

    ; Ensrick compatibility fix: Location may validly be None during transitions.
    Bool newIsRegion = false
    Bool oldWasRegion = false

    utility.wait(0.200000)
    inMede = false
    inOut = false
    if akNewLoc
        newIsRegion = akNewLoc.hasKeywordString("isMedeMoney")
    endIf
    if akOldLoc
        oldWasRegion = akOldLoc.hasKeywordString("isMedeMoney")
    endIf
    if newIsRegion
        busy = true
        inOut = true
        inMede = true
        dialAlt = false
        if !oldWasRegion
            amountA = PlayerRef.GetItemCount(Gold001 as form)
            amountB = PlayerRef.GetItemCount(altCoins as form)
            self.altConversion()
        else
            self.goldCheck()
        endIf
        altCoins = Mede
        coinsName = Mede.getName()
        MoneyName.setName(coinsName)
        Gold001.setName(coinsName)
        busy = false
        dialAlt = true
    endIf
endFunction

function OnPlayerLoadGame()

    if inMede
        MoneyName.setName(Mede.getName())
        dialAlt = true
    endIf
endFunction

function OnMenuOpen(String MenuName)

    if inMede == true
        dialAlt = false
        PlayerRef.AddPerk(medePerk)
        if MenuName == "InventoryMenu"
            self.goldCheck()
        elseIf MenuName == "Dialogue Menu" || MenuName == "BarterMenu" && !dial
            self.goldCheck()
            self.openMenu()
        elseIf MenuName == "ContainerMenu" || MenuName == "GiftMenu"
            self.containerSwitch()
        elseIf MenuName == "Crafting Menu"
            self.craftingMethod()
        endIf
    endIf
endFunction

; Skipped compiler generated GotoState

; Skipped compiler generated GetState

function OnMenuClose(String MenuName)

    if inMede == true
        busy = true
        PlayerRef.RemovePerk(medePerk)
        if MenuName == "Dialogue Menu" || MenuName == "BarterMenu" && !dial || MenuName == "Crafting Menu" && craft as Bool
            self.closeMenu()
        elseIf MenuName == "Crafting Menu"
            self.exitCraftingCalc()
        elseIf MenuName == "InventoryMenu"
            dialAlt = true
        endIf
        busy = false
        self.refresh()
        dialAlt = true
    endIf
endFunction

