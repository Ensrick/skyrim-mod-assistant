;/ Decompiled by Champollion V1.0.1
Source   : EC_septimsScript.psc
Modified : 2026-05-28 00:29:44
Compiled : 2026-05-28 00:38:01
User     : victo
Computer : LAPTOP-5P8G2UR1
/;
scriptName ec_septimsscript extends EC_septimsFunctions

;-- Properties --------------------------------------

;-- Variables ---------------------------------------
Bool boolcontainer
Bool inSky
Bool dont
Bool dialBis
Bool busy

;-- Functions ---------------------------------------

function OnMenuOpen(String MenuName)

    while busy != false
        utility.WaitMenuMode(0.100000)
    endWhile
    self.checkMintExchanger()
    if MintExchanger
        inSky = true
    endIf
    if inSky
        dialBis = false
        busy = true
        if MenuName == "InventoryMenu" && !MintExchanger
            self.goldCheck()
        elseIf MenuName == "Dialogue Menu"
            if MintExchanger
                self.locationSwitch()
            else
                self.goldCheck()
            endIf
            self.countallseptims()
            dial = true
        elseIf MenuName == "BarterMenu" && dial == false
            self.goldCheck()
            self.countallseptims()
            utility.wait(0.200000)
            while utility.IsInMenuMode()
                utility.wait(0.100000)
            endWhile
            totalNow = PlayerRef.GetItemCount(gold001 as form)
            if totalNow > totalValue
                self.getBenefice()
            elseIf totalNow < totalValue
                sum = totalValue - totalNow
                self.getInvest()
            endIf
        elseIf MenuName == "BarterMenu" && dial == true
            barter = true
            while utility.IsInMenuMode()
                utility.wait(0.100000)
            endWhile
        elseIf MenuName == "Crafting Menu" && dial == true
            craft = true
            self.countallseptims()
            while utility.IsInMenuMode()
                utility.wait(0.100000)
            endWhile
        elseIf (MenuName == "containerMenu" || MenuName == "GiftMenu") && !MintExchanger
            boolcontainer = true
            self.goldCheck()
            if (game.GetCurrentCrosshairRef() as actor) as Bool
                self.septimsOnActor()
            endIf
            while utility.IsInMenuMode()
                utility.wait(0.100000)
            endWhile
            self.countallseptims()
            if !dial
                dialBis = true
                boolcontainer = false
            endIf
        endIf
        busy = false
    endIf
endFunction

function OnMenuClose(String MenuName)

    while busy != false
        utility.WaitMenuMode(0.100000)
    endWhile
    if inSky
        utility.wait(0.200000)
        busy = true
        if MenuName == "Dialogue Menu" && !craft || MenuName == "Crafting Menu" && craft == true
            if !boolcontainer
                totalNow = PlayerRef.GetItemCount(gold001 as form)
                if totalNow > totalValue
                    if craft == true
                        self.craftConversion()
                    else
                        self.getBenefice()
                    endIf
                elseIf totalNow < totalValue
                    sum = totalValue - totalNow
                    self.getInvest()
                endIf
                dialBis = true
            else
                boolcontainer = false
            endIf
            if dial as Bool && !craft
                dial = false
            endIf
            if craft
                craft = false
            endIf
            if barter == true
                barter = false
            endIf
        endIf
        busy = false
        self.refresh()
    endIf
    if MenuName == "InventoryMenu"
        dialBis = true
    endIf
    if MintExchanger
        inSky = false
        MintExchanger = false
        ActorName = "XoXo"
    endIf
endFunction

function OnLocationChange(location akOldLoc, location akNewLoc)

    ; Ensrick compatibility fix: Location may validly be None during transitions.
    Bool newUsesRegionalCurrency = false
    Bool oldUsedRegionalCurrency = false

    busy = true
    dialBis = false
    inSky = false
    if akNewLoc
        newUsesRegionalCurrency = akNewLoc.hasKeywordString("isUlfmoney") || akNewLoc.hasKeywordString("isDramMoney") || akNewLoc.hasKeywordString("isDrakrMoney") || akNewLoc.hasKeywordString("isMedeMoney") || akNewLoc.hasKeywordString("isOshMoney") || akNewLoc.hasKeywordString("isOhzermoney") || akNewLoc.hasKeywordString("isVarkenMoney")
    endIf
    if akOldLoc
        oldUsedRegionalCurrency = akOldLoc.hasKeywordString("isUlfmoney") || akOldLoc.hasKeywordString("isDramMoney") || akOldLoc.hasKeywordString("isDrakrMoney") || akOldLoc.hasKeywordString("isMedeMoney") || akOldLoc.hasKeywordString("isOshMoney") || akOldLoc.hasKeywordString("isOhzermoney") || akOldLoc.hasKeywordString("isVarkenMoney")
    endIf
    if !newUsesRegionalCurrency
        inSky = true
        if oldUsedRegionalCurrency
            self.locationSwitch()
        else
            self.goldCheck()
        endIf
        gold001.setName(nSeptim + "s ")
        MoneyName.setName(nSeptim)
    endIf
    utility.wait(0.200000)
    dialBis = true
    busy = false
endFunction

; Skipped compiler generated GotoState

function OnPlayerLoadGame()

    vCopper = gold004.getGoldValue()
    vSilver = gold002.getGoldValue()
    vGold = gold003.getGoldValue()
    nCopper = gold004.getname()
    nSilver = gold002.getname()
    nGold = gold003.getname()
    nSeptim = "Septim"
    if inSky
        gold001.setName(nSeptim + "s ")
        MoneyName.setName(nSeptim)
    endIf
    dialBis = true
    self.refresh()
endFunction

; Skipped compiler generated GetState

function OnItemremoved(form akBaseItem, Int aiItemCount, objectreference akItemReference, objectreference akDestContainer)

    if akBaseItem == gold001 as form
        if dialBis == true && inSky as Bool && !craft
            self.countallseptims()
            sum = aiItemCount
            self.getInvest()
            utility.wait(0.200000)
        endIf
        if ui.IsMenuOpen("containerMenu") && inSky as Bool && !dont
            akDestContainer.removeitem(gold001 as form, aiItemCount, true, none)
            PlayerRef.AddItem(gold001 as form, aiItemCount, true)
            DontSeptimInstance.show(0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000)
        endIf
        utility.WaitMenuMode(0.100000)
        dont = false
    endIf
    if akBaseItem == gold004 as form
        if ui.IsMenuOpen("InventoryMenu") && inSky as Bool
            PlayerRef.removeitem(gold001 as form, aiItemCount * vCopper, true, none)
            utility.WaitMenuMode(0.100000)
        endIf
        if ui.IsMenuOpen("containerMenu") && inSky as Bool
            while dont
                utility.WaitMenuMode(0.100000)
            endWhile
            dont = true
            PlayerRef.removeitem(gold001 as form, aiItemCount * vCopper, true, none)
        endIf
    endIf
    if akBaseItem == gold003 as form
        if ui.IsMenuOpen("InventoryMenu") && inSky as Bool
            PlayerRef.removeitem(gold001 as form, aiItemCount * vGold, true, none)
            utility.WaitMenuMode(0.100000)
        endIf
        if ui.IsMenuOpen("containerMenu") && inSky as Bool
            while dont
                utility.WaitMenuMode(0.100000)
            endWhile
            dont = true
            PlayerRef.removeitem(gold001 as form, aiItemCount * vGold, true, none)
        endIf
    endIf
    if akBaseItem == gold002 as form
        if ui.IsMenuOpen("InventoryMenu") && inSky as Bool
            PlayerRef.removeitem(gold001 as form, aiItemCount * vSilver, true, none)
            utility.WaitMenuMode(0.100000)
        endIf
        if ui.IsMenuOpen("containerMenu") && inSky as Bool
            while dont
                utility.WaitMenuMode(0.100000)
            endWhile
            dont = true
            PlayerRef.removeitem(gold001 as form, aiItemCount * vSilver, true, none)
        endIf
    endIf
endFunction

function OnInit()

    self.refresh()
    vCopper = gold004.getGoldValue()
    vSilver = gold002.getGoldValue()
    vGold = gold003.getGoldValue()
    nCopper = gold004.getname()
    nSilver = gold002.getname()
    nGold = gold003.getname()
    nSeptim = "Septim"
    dialBis = true
endFunction

function OnKeyDown(Int KeyCode)

    if craft == true
        if KeyCode == 46 || KeyCode == 31 || KeyCode == 34
            code = KeyCode
            conversion = true
            if KeyCode == 46
                CopperConversion.show(0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000)
            elseIf KeyCode == 31
                SilverConversion.show(0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000)
            elseIf KeyCode == 34
                GoldConversion.show(0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000, 0.000000)
            endIf
        endIf
    endIf
endFunction

function OnItemAdded(form akBaseItem, Int aiItemCount, objectreference akItemReference, objectreference akSourceContainer)

    if akBaseItem == gold001 as form
        if dialBis == true && inSky as Bool && !craft
            sum = aiItemCount
            self.getBeneficeBis()
            utility.wait(0.200000)
        endIf
    endIf
    if akBaseItem == gold004 as form
        if ui.IsMenuOpen("containerMenu") && inSky as Bool
            PlayerRef.AddItem(gold001 as form, aiItemCount, true)
        endIf
    endIf
    if akBaseItem == gold003 as form
        if ui.IsMenuOpen("containerMenu") && inSky as Bool
            PlayerRef.AddItem(gold001 as form, aiItemCount * vGold, true)
        endIf
    endIf
    if akBaseItem == gold002 as form
        if ui.IsMenuOpen("containerMenu") && inSky as Bool
            PlayerRef.AddItem(gold001 as form, aiItemCount * vSilver, true)
        endIf
    endIf
endFunction

