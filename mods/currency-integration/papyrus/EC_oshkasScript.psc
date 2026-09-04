;/ Decompiled by Champollion V1.0.1
Source   : EC_oshkasScript.psc
Modified : 2026-05-27 18:35:08
Compiled : 2026-05-27 18:36:58
User     : victo
Computer : LAPTOP-5P8G2UR1
/;
scriptName EC_oshkasScript extends EC_altCurrencyFunctions

;-- Properties --------------------------------------
perk property OshkaPerk auto
miscobject property Oshka auto

;-- Variables ---------------------------------------
Bool inOsh

;-- Functions ---------------------------------------

; Skipped compiler generated GotoState

function OnPlayerLoadGame()

    if inOsh
        MoneyName.setName(Oshka.getName())
        dialAlt = true
    endIf
endFunction

function OnMenuClose(String MenuName)

    if inOsh == true
        busy = true
        PlayerRef.RemovePerk(OshkaPerk)
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

; Skipped compiler generated GetState

function OnMenuOpen(String MenuName)

    if inOsh == true
        self.checkMintExchanger()
        dialAlt = false
        PlayerRef.AddPerk(OshkaPerk)
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

function OnLocationChange(location akOldLoc, location akNewLoc)

    ; Ensrick compatibility fix: Location may validly be None during transitions.
    Bool newIsRegion = false
    Bool oldWasRegion = false

    utility.wait(0.200000)
    inOsh = false
    inOut = false
    if akNewLoc
        newIsRegion = akNewLoc.hasKeywordString("isOshMoney")
    endIf
    if akOldLoc
        oldWasRegion = akOldLoc.hasKeywordString("isOshMoney")
    endIf
    if newIsRegion
        busy = true
        inOut = true
        inOsh = true
        dialAlt = false
        if !oldWasRegion
            amountA = PlayerRef.GetItemCount(Gold001 as form)
            amountB = PlayerRef.GetItemCount(altCoins as form)
            self.altConversion()
        else
            self.goldCheck()
        endIf
        altCoins = Oshka
        coinsName = Oshka.getName()
        MoneyName.setName(coinsName)
        Gold001.setName(coinsName)
        busy = false
        dialAlt = true
    endIf
endFunction

