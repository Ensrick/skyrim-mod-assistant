Scriptname DES_UlfricCurrencySwapper extends DES_CurrencyFramework_UtilityInt
{Cost-only M.I.N.T. compatibility implementation. Currency ownership belongs to EnsrickCurrencyDenominations.}

DES_CurrencyFramework_Functions Property CurrencyFunctions Auto
Actor Property PlayerRef Auto
MiscObject Property DES_Ulfric Auto
FormList Property DES_CustomCurrencyLocations Auto
Keyword Property CWOwner Auto
Location Property WindhelmLocation Auto
Location Property SolitudeLocation Auto
GlobalVariable Property CWSons Auto
GlobalVariable Property CWImperial Auto
GlobalVariable Property DES_UlfricWorth Auto
GlobalVariable[] Property CostsToUpdate Auto
Int[] Property defaultCosts Auto
GlobalVariable Property RoomCost Auto
GlobalVariable Property DES_UlfricRoomCost Auto
GlobalVariable Property HorseCost Auto
GlobalVariable Property DES_UlfricHorseCost Auto
Quest Property HousePurchase Auto
FormList Property DES_UlfricLocations Auto
Perk Property DES_WindhelmPriceAdjustmentPerk Auto

Function Initialize()
    If DES_CustomCurrencyLocations && WindhelmLocation && !DES_CustomCurrencyLocations.HasForm(WindhelmLocation)
        DES_CustomCurrencyLocations.AddForm(WindhelmLocation)
    EndIf
EndFunction

Function UpdateCosts()
    If !DES_UlfricWorth
        Return
    EndIf
    If WindhelmLocation && CWOwner && CWImperial && WindhelmLocation.GetKeywordData(CWOwner) == CWImperial.GetValue() as Int
        DES_UlfricWorth.SetValue(2.0)
    ElseIf SolitudeLocation && CWOwner && CWSons && SolitudeLocation.GetKeywordData(CWOwner) == CWSons.GetValue() as Int
        DES_UlfricWorth.SetValue(1.0)
    Else
        DES_UlfricWorth.SetValue(1.25)
    EndIf

    Float ulfricValue = DES_UlfricWorth.GetValue()
    If CostsToUpdate && defaultCosts && HousePurchase
        Int limit = CostsToUpdate.Length
        If defaultCosts.Length < limit
            limit = defaultCosts.Length
        EndIf
        Int index = 0
        While index < limit
            If CostsToUpdate[index]
                CostsToUpdate[index].SetValueInt(Math.Ceiling(defaultCosts[index] * ulfricValue))
                HousePurchase.UpdateCurrentInstanceGlobal(CostsToUpdate[index])
            EndIf
            index += 1
        EndWhile
    EndIf
    If RoomCost && DES_UlfricRoomCost
        DES_UlfricRoomCost.SetValueInt(Math.Ceiling(RoomCost.GetValue() * ulfricValue))
        UpdateCurrentInstanceGlobal(DES_UlfricRoomCost)
    EndIf
    If HorseCost && DES_UlfricHorseCost
        DES_UlfricHorseCost.SetValueInt(Math.Ceiling(HorseCost.GetValue() * ulfricValue))
        UpdateCurrentInstanceGlobal(DES_UlfricHorseCost)
    EndIf
EndFunction

Event OnInit()
    Utility.Wait(1.0)
    Initialize()
    UpdateCosts()
EndEvent

Function OnPlayerLoadGame_Alias()
    Initialize()
    UpdateCosts()
EndFunction

Function OnLocationChange_Alias()
    UpdateCosts()
EndFunction

