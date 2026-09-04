;/ Decompiled by Champollion V1.0.1
Source   : EC_drakrsScript.psc
Modified : 2026-05-20 20:56:56
Compiled : 2026-05-20 20:57:25
User     : victo
Computer : LAPTOP-5P8G2UR1
/;
scriptName EC_drakrsScript extends EC_altCurrencyFunctions

;-- Properties --------------------------------------
perk property drakrPerk auto
miscobject property Drakr auto

;-- Variables ---------------------------------------
Bool inDrak

;-- Functions ---------------------------------------

; Skipped compiler generated GetState

function OnLocationChange(location akOldLoc, location akNewLoc)

    ; Ensrick compatibility fix: Location may validly be None during transitions.
    Bool newIsRegion = false
    Bool oldWasRegion = false

    utility.wait(0.200000)
    inDrak = false
    inOut = false
    if akNewLoc
        newIsRegion = akNewLoc.hasKeywordString("isDrakrMoney")
    endIf
    if akOldLoc
        oldWasRegion = akOldLoc.hasKeywordString("isDrakrMoney")
    endIf
    if newIsRegion
        busy = true
        inOut = true
        inDrak = true
        dialAlt = false
        if !oldWasRegion
            amountA = PlayerRef.GetItemCount(Gold001 as form)
            amountB = PlayerRef.GetItemCount(altCoins as form)
            self.altConversion()
        else
            self.goldCheck()
        endIf
        altCoins = Drakr
        coinsName = Drakr.getName()
        MoneyName.setName(coinsName)
        Gold001.setName(coinsName)
        busy = false
        dialAlt = true
    endIf
endFunction

; Skipped compiler generated GotoState

function OnMenuClose(String MenuName)

    if inDrak == true
        busy = true
        PlayerRef.RemovePerk(drakrPerk)
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

function OnPlayerLoadGame()

    if inDrak
        MoneyName.setName(Drakr.getName())
        dialAlt = true
    endIf
endFunction

function OnMenuOpen(String MenuName)

    if inDrak == true
        self.checkMintExchanger()
        dialAlt = false
        PlayerRef.AddPerk(drakrPerk)
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

