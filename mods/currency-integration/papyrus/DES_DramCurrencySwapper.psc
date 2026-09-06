Scriptname DES_DramCurrencySwapper extends DES_CurrencyFramework_UtilityInt Conditional
{Cost/stage-only M.I.N.T. compatibility implementation. Currency ownership belongs to EnsrickCurrencyDenominations.}

DES_CurrencyFramework_Functions Property CurrencyFunctions Auto
Actor Property PlayerRef Auto
MiscObject Property DES_Dram Auto
FormList Property DES_CustomCurrencyLocations Auto
Location Property DLC2RavenRockLocation Auto
Location Property DLC2TelMithrynLocation Auto
GlobalVariable Property RoomCost Auto
GlobalVariable Property DES_DramRoomCost Auto
GlobalVariable Property DES_UlfricChanceNone Auto
GlobalVariable Property DES_DramWorth Auto
FormList Property DES_DramLocations Auto
Perk Property DES_MorrowindPriceAdjustmentPerk Auto

Function Initialize()
    If DES_CustomCurrencyLocations && DLC2RavenRockLocation && !DES_CustomCurrencyLocations.HasForm(DLC2RavenRockLocation)
        DES_CustomCurrencyLocations.AddForm(DLC2RavenRockLocation)
    EndIf
    If DES_CustomCurrencyLocations && DLC2TelMithrynLocation && !DES_CustomCurrencyLocations.HasForm(DLC2TelMithrynLocation)
        DES_CustomCurrencyLocations.AddForm(DLC2TelMithrynLocation)
    EndIf
    If DES_UlfricChanceNone && Game.IsPluginInstalled("WindhelmUsesUlfrics.esp")
        DES_UlfricChanceNone.SetValue(0.0)
    EndIf
EndFunction

Function UpdateCosts()
    If RoomCost && DES_DramRoomCost && DES_DramWorth
        Int dramRoomCost = Math.Ceiling(RoomCost.GetValue() * DES_DramWorth.GetValue())
        DES_DramRoomCost.SetValueInt(dramRoomCost)
        UpdateCurrentInstanceGlobal(DES_DramRoomCost)
    EndIf
    Quest ulfricServices = Quest.GetQuest("DES_UlfricWindhelmServicesQuest")
    If ulfricServices
        Ulfric = ulfricServices.GetStage()
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
    If IsStageDone(0) && PlayerRef && DLC2RavenRockLocation && !PlayerRef.IsInLocation(DLC2RavenRockLocation)
        SetStage(6)
    EndIf
EndFunction

Int Property Trespassing Auto Conditional
Int Property Ulfric Auto Conditional
