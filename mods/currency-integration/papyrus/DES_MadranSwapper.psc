Scriptname DES_MadranSwapper extends ReferenceAlias
{Inert loader-compatible class for ECE's removed Ma'dran transaction attachment.}

DES_CurrencyFramework_Functions Property CurrencyFunctions Auto
MiscObject Property DES_Ulfric Auto
FormList Property DES_UlfricLocations Auto
Perk Property DES_WindhelmPriceAdjustmentPerk Auto

; Intentionally no events and no calls into Currency Swapper. The winning QUST
; removes this alias attachment; this same-name class only makes stale old-save
; instances harmless while EnsrickCurrencyDenominations owns the ledger.
