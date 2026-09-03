Scriptname Ensrick_CurrencyRuntimeDefaultsAlias extends ReferenceAlias

DES_CoinManager Property CoinManager Auto
Quest Property MintFramework Auto
GlobalVariable Property MintAutoConvert Auto

Int _bootPass = 0
Bool _successLogged = False
Bool _exhaustionLogged = False

Event OnInit()
	InitializePolicy()
EndEvent

Event OnPlayerLoadGame()
	InitializePolicy()
EndEvent

Event OnUpdate()
	Bool coinPolicyApplied = ApplyPolicy()
	_bootPass += 1

	If _bootPass < 4
		If _bootPass == 1
			RegisterForSingleUpdate(5.0)
		ElseIf _bootPass == 2
			RegisterForSingleUpdate(15.0)
		Else
			RegisterForSingleUpdate(30.0)
		EndIf
	ElseIf !coinPolicyApplied && !_exhaustionLogged
		Debug.Trace("[EnsrickCurrency] C.O.I.N. runtime-default enforcement exhausted its bounded boot retries; Journal Menu close remains armed.")
		_exhaustionLogged = True
	EndIf
EndEvent

Event OnMenuClose(String MenuName)
	If MenuName == "Journal Menu"
		ApplyPolicy()
	EndIf
EndEvent

Function InitializePolicy()
	UnregisterForMenu("Journal Menu")
	RegisterForMenu("Journal Menu")
	_bootPass = 0
	_successLogged = False
	_exhaustionLogged = False
	ApplyPolicy()
	RegisterForSingleUpdate(1.0)
EndFunction

Bool Function ApplyPolicy()
	If MintFramework && MintAutoConvert
		MintAutoConvert.SetValue(0.0)
	EndIf

	If CoinManager && CoinManager.ready && CoinManager.PlayerAlias
		CoinManager.PlayerAlias.autoExchange = False
		CoinManager.PlayerAlias.verbose = False
		If !_successLogged
			Debug.Trace("[EnsrickCurrency] Enforced physical-currency defaults: C.O.I.N. autoExchange=false, verbose=false; M.I.N.T. conversion=0.")
			_successLogged = True
		EndIf
		Return True
	EndIf

	Return False
EndFunction
