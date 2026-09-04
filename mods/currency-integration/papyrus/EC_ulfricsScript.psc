;/ Decompiled by Champollion V1.0.1
Source   : EC_ulfricsScript.psc
Modified : 2026-05-20 20:57:04
Compiled : 2026-05-20 20:57:25
User     : victo
Computer : LAPTOP-5P8G2UR1
/;
scriptName EC_ulfricsScript extends EC_altCurrencyFunctions

;-- Properties --------------------------------------
miscobject property Ulfric auto
perk property ulfricPerk auto

;-- Variables ---------------------------------------
Bool inWind

;-- Functions ---------------------------------------

function OnLocationChange(location akOldLoc, location akNewLoc)

    ; Ensrick compatibility fix: Location may validly be None during transitions.
    Bool newIsRegion = false
    Bool oldWasRegion = false

    utility.wait(0.200000)
    inWind = false
    inOut = false
    if akNewLoc
        newIsRegion = akNewLoc.hasKeywordString("isUlfMoney")
    endIf
    if akOldLoc
        oldWasRegion = akOldLoc.hasKeywordString("isUlfMoney")
    endIf
    if newIsRegion
        busy = true
        inOut = true
        inWind = true
        dialAlt = false
        if !oldWasRegion
            amountA = PlayerRef.GetItemCount(Gold001 as form)
            amountB = PlayerRef.GetItemCount(altCoins as form)
            self.altConversion()
        else
            self.goldCheck()
        endIf
        altCoins = Ulfric
        coinsName = Ulfric.getName()
        MoneyName.setName(coinsName)
        Gold001.setName(coinsName)
        busy = false
        dialAlt = true
    endIf
endFunction

function OnPlayerLoadGame()

    if inWind
        MoneyName.setName(Ulfric.getName())
        dialAlt = true
    endIf
endFunction

function OnMenuOpen(String MenuName)

    if inWind == true
        self.checkMintExchanger()
        dialAlt = false
        PlayerRef.AddPerk(ulfricPerk)
        if MenuName == "InventoryMenu"
            self.goldCheck()
        elseIf MenuName == "Dialogue Menu" || MenuName == "BarterMenu" && !dial
            if !MintExchanger
                self.goldCheck()
                self.openMenu()
            endIf
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

    if inWind == true
        busy = true
        PlayerRef.RemovePerk(ulfricPerk)
        if MenuName == "Dialogue Menu" || MenuName == "BarterMenu" && !dial || MenuName == "Crafting Menu" && craft as Bool
            if MintExchanger
                self.ExitMintExchanger()
            else
                self.closeMenu()
                dialAlt = true
            endIf
        elseIf MenuName == "Crafting Menu"
            self.exitCraftingCalc()
        elseIf MenuName == "InventoryMenu"
            dialAlt = true
        endIf
        busy = false
        self.refresh()
    endIf
endFunction

