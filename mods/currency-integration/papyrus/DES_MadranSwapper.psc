Scriptname DES_MadranSwapper extends DES_CurrencyFramework_BarterExclusion
{Compatibility class for ECE's obsolete M.I.N.T. Ma'dran VMAD attachment.}

; Independently authored by Ensrick. The legacy class and property identifiers
; are retained solely so the released ECE patch can resolve its stale VMAD
; while the winning owned plugin migrates the live alias to M.I.N.T. 1.0.6's
; DES_CurrencyFramework_BarterExclusion class.

MiscObject Property DES_Ulfric Auto
FormList Property DES_UlfricLocations Auto
Perk Property DES_WindhelmPriceAdjustmentPerk Auto

Event OnInit()
    ; This path is defensive for an old save or transient source attachment.
    ; The current winning alias uses the parent class and its modern properties
    ; directly, so the shim normally exists only to satisfy the class loader.
    akCurrency = DES_Ulfric
    akSwapLocations = DES_UlfricLocations
    akPriceMod = DES_WindhelmPriceAdjustmentPerk
    If PlayerRef == None
        PlayerRef = Game.GetPlayer()
    EndIf
EndEvent
