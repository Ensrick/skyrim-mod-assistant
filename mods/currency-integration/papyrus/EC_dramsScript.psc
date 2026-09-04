;/ Decompiled by Champollion V1.0.1
Source   : EC_dramsScript.psc
Modified : 2026-05-20 20:56:51
Compiled : 2026-05-20 20:57:25
User     : victo
Computer : LAPTOP-5P8G2UR1
/;
scriptName EC_dramsScript extends EC_altCurrencyFunctions

;-- Properties --------------------------------------
perk property dramPerk auto
miscobject property Dram auto

;-- Variables ---------------------------------------
Bool inDram

;-- Functions ---------------------------------------

; Skipped compiler generated GotoState

function OnMenuOpen(String MenuName)

    if inDram == true
        self.checkMintExchanger()
        dialAlt = false
        PlayerRef.AddPerk(dramPerk)
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

; Skipped compiler generated GetState

function OnMenuClose(String MenuName)

    if inDram == true
        busy = true
        PlayerRef.RemovePerk(dramPerk)
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

function OnLocationChange(location akOldLoc, location akNewLoc)

    ; Ensrick compatibility fix: Location may validly be None during transitions.
    Bool newIsRegion = false
    Bool oldWasRegion = false

    utility.wait(0.200000)
    inDram = false
    inOut = false
    if akNewLoc
        newIsRegion = akNewLoc.hasKeywordString("isDramMoney")
    endIf
    if akOldLoc
        oldWasRegion = akOldLoc.hasKeywordString("isDramMoney")
    endIf
    if newIsRegion
        busy = true
        inOut = true
        inDram = true
        dialAlt = false
        if !oldWasRegion
            amountA = PlayerRef.GetItemCount(Gold001 as form)
            amountB = PlayerRef.GetItemCount(altCoins as form)
            self.altConversion()
        else
            self.goldCheck()
        endIf
        altCoins = Dram
        coinsName = Dram.getName()
        MoneyName.setName(coinsName)
        Gold001.setName(coinsName)
        busy = false
        dialAlt = true
    endIf
endFunction

function OnPlayerLoadGame()

    if inDram
        MoneyName.setName(Dram.getName())
        dialAlt = true
    endIf
endFunction

