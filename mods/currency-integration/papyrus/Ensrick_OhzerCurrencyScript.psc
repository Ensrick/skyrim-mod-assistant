Scriptname Ensrick_OhzerCurrencyScript extends EC_altCurrencyFunctions

; Interoperability derivative of ECE's EC_oshkasScript transaction flow.
; This file is excluded from the repository/package MIT grant. Redistribution
; is governed by Exchange Currency Enhanced's Nexus permissions; credit ECE.
;
; ECE defines and distributes Ohzer but does not ship a transaction alias for it.
; Ohzer is intentionally neutral-rate, so unlike currencies with a regional
; exchange-rate adjustment it does not add a barter-price perk.

MiscObject Property Ohzer Auto
Keyword Property OhzerMoneyKeyword Auto

Bool inOhzer = False

Event OnInit()
    altCoins = Ohzer
    refresh()
    dialAlt = True
    Location currentLocation = PlayerRef.GetCurrentLocation()
    If currentLocation && currentLocation.HasKeyword(OhzerMoneyKeyword)
        ApplyOhzerState(None, currentLocation)
    EndIf
EndEvent

Event OnLocationChange(Location akOldLoc, Location akNewLoc)
    Utility.Wait(0.2)
    ApplyOhzerState(akOldLoc, akNewLoc)
EndEvent

Function ApplyOhzerState(Location akOldLoc, Location akNewLoc)
    inOhzer = False
    inOut = False

    If akNewLoc && akNewLoc.HasKeyword(OhzerMoneyKeyword)
        busy = True
        inOut = True
        inOhzer = True
        dialAlt = False
        altCoins = Ohzer
        coinsName = Ohzer.GetName()
        If !akOldLoc || !akOldLoc.HasKeyword(OhzerMoneyKeyword)
            amountA = PlayerRef.GetItemCount(Gold001 as Form)
            amountB = PlayerRef.GetItemCount(altCoins as Form)
            altConversion()
        Else
            goldCheck()
        EndIf
        MoneyName.SetName(coinsName)
        Gold001.SetName(coinsName)
        busy = False
        dialAlt = True
    EndIf
EndFunction

Event OnPlayerLoadGame()
    altCoins = Ohzer
    Location currentLocation = PlayerRef.GetCurrentLocation()
    If currentLocation && currentLocation.HasKeyword(OhzerMoneyKeyword)
        If inOhzer
            ApplyOhzerState(currentLocation, currentLocation)
        Else
            ApplyOhzerState(None, currentLocation)
        EndIf
    Else
        inOhzer = False
        inOut = False
    EndIf
    dialAlt = True
    refresh()
EndEvent

Event OnMenuOpen(String menuName)
    If inOhzer
        dialAlt = False
        If menuName == "InventoryMenu"
            goldCheck()
        ElseIf menuName == "Dialogue Menu" || (menuName == "BarterMenu" && !dial)
            goldCheck()
            openMenu()
        ElseIf menuName == "ContainerMenu" || menuName == "GiftMenu"
            containerSwitch()
        ElseIf menuName == "Crafting Menu"
            craftingMethod()
        EndIf
    EndIf
EndEvent

Event OnMenuClose(String menuName)
    If inOhzer
        busy = True
        If menuName == "Dialogue Menu" || (menuName == "BarterMenu" && !dial) || (menuName == "Crafting Menu" && craft)
            closeMenu()
            dialAlt = True
        ElseIf menuName == "Crafting Menu"
            exitCraftingCalc()
        ElseIf menuName == "InventoryMenu"
            dialAlt = True
        EndIf
        busy = False
        refresh()
    EndIf
EndEvent
