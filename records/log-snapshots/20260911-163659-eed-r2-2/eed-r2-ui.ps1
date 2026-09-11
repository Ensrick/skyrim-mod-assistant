# EED R2 verification driver: fresh character through Skyrim Unbound, via MenuPilot.
# Adapted from records/log-snapshots/20260910-231046-eed-r1/eed-r1-ui.ps1 (R1) and
# the verified quit recipe in docs/MENUPILOT.md. One action per call so every step
# is observable and the caller decides the next one from the readback.
param(
  [Parameter(Mandatory)][int]$OwnedPid,
  [ValidateSet('Main','MainNew','New','Race','MCM','Pages','Page','Keys','Open','Options','Nav','Accept','Read','Begin','Ping','Quit','Dump','Inventory')][string]$Action,
  [string]$Key='Down',
  [int]$Count=1,
  [string]$Expect='',
  [string]$Path='',
  [string]$Menu='Journal Menu',
  [string]$ClaimOwner='fable/eed-r2'
)
$ErrorActionPreference='Stop'
$py='C:\Users\danjo\AppData\Local\Programs\Python\Python313\python.exe'
$root='C:\Users\danjo\source\repos\skyrim-mod-assistant'
$live=Get-Process SkyrimSE -ErrorAction Stop
if(@($live).Count -ne 1 -or $live.Id -ne $OwnedPid){throw 'Unexpected game process set'}
$claim=& $py "$root\audit\claim.py" check --owner $ClaimOwner
if($LASTEXITCODE -ne 0 -or $claim -notmatch '^mine:'){throw 'Claim missing'}
function Cmd($op,$fields=@{}){@{op=$op}+$fields|ConvertTo-Json -Compress -Depth 6}
$codes=@{Accept=28;Down=208;Up=200;Left=203;Right=205;Journal=36;Cancel=1;Tween=15}
function Tap($name){Cmd 'input.tap' @{event=$name;code=$codes[$name]}}
function ReadField($menu,$path){Cmd 'gfx.get' @{menu=$menu;path=$path}}
function InvokeField($menu,$path){Cmd 'gfx.invoke' @{menu=$menu;method=$path;args=@()}}
function Step([string[]]$commands,[string]$expected=''){
 $out=& $py "$root\audit\menupilot.py" send @commands --timeout 25
 $out|Select-String 'RESULT|BATCH_DONE|ERROR'|ForEach-Object Line
 if($LASTEXITCODE -ne 0){throw ($out -join "`n")}
 if($expected -and -not(($out -join "`n").Contains('value="'+$expected+'"'))){throw "Expected $expected"}
}
$wait=Cmd 'wait' @{ms=400}
$main='_root.MenuHolder.Menu_mc'
$race='_root.RaceSexMenuBaseInstance.RaceSexPanelsInstance'
$journal='_root.QuestJournalFader.Menu_mc'
$page="$journal.SystemFader.Page_mc"
$config="$journal.ConfigPanel"
switch($Action){
 'Main'{ Step @((Cmd 'menu.list'),(ReadField 'Main Menu' "$main.MainList.selectedEntry.text")) }
 # Walk down until $NEW is selected (a fresh clone profile starts on $NEW; one
 # with saves starts on $CONTINUE). At most three presses.
 'MainNew'{
  $out=& $py "$root\audit\menupilot.py" send (ReadField 'Main Menu' "$main.MainList.selectedEntry.text") --timeout 25
  $out|Select-String 'RESULT'|ForEach-Object Line
  $tries=0
  while(-not(($out -join "`n").Contains('value="$NEW"')) -and $tries -lt 3){
   $tries++
   $out=& $py "$root\audit\menupilot.py" send (Tap 'Down') $wait (ReadField 'Main Menu' "$main.MainList.selectedEntry.text") --timeout 25
   $out|Select-String 'RESULT'|ForEach-Object Line
  }
  if(-not(($out -join "`n").Contains('value="$NEW"'))){throw 'Could not reach $NEW'}
 }
 'New'{
  Step @((ReadField 'Main Menu' "$main.MainList.selectedEntry.text")) '$NEW'
  Step @((Tap 'Accept'),$wait,(ReadField 'Main Menu' "$main.ConfirmPanel_mc.textField.text")) 'Start a new game?'
  Step @((Tap 'Accept'))
 }
 'Race'{
  Step @((ReadField 'RaceSex Menu' "$race.bottomBar.buttonPanel.button0.textField.text"))
  Step @((InvokeField 'RaceSex Menu' "$race.bottomBar.buttonPanel.button0.onPress"),(InvokeField 'RaceSex Menu' "$race.bottomBar.buttonPanel.button0.onRelease"),$wait,(ReadField 'MessageBoxMenu' '_root.MessageMenu.MessageText.text')) 'Finish and name your character?'
  Step @((Tap 'Accept'),$wait,(ReadField 'RaceSex Menu' "$race.textEntry._visible")) 'true'
  Step @((ReadField 'RaceSex Menu' "$race.textEntry.TextInputInstance.textField.text")) 'Adventurer'
  Step @((Tap 'Accept'))
 }
 'MCM'{
  Step @((Tap 'Journal'),$wait,(InvokeField 'Journal Menu' "$journal.SystemTab.onPress"),(InvokeField 'Journal Menu' "$journal.SystemTab.onRelease"),(ReadField 'Journal Menu' "$page.CategoryList_mc.List_mc.iSelectedIndex")) '0'
  Step ((@((Tap 'Down'))*6)+@((ReadField 'Journal Menu' "$page.CategoryList_mc.List_mc.selectedEntry.text"))) '$MOD CONFIGURATION'
  Step @((Tap 'Accept'),$wait,(ReadField 'Journal Menu' "$config._modList._entryList.0.text")) ' Skyrim Unbound'
  Step @((Tap 'Down'),(Tap 'Accept'),$wait,(ReadField 'Journal Menu' "$config._subList._entryList.1.text")) 'Starting Location'
 }
 'Pages'{ Step @((Cmd 'gfx.dump' @{menu='Journal Menu';path="$config._subList._entryList";depth=2;max=60}),(ReadField 'Journal Menu' "$config._subList._selectedIndex")) }
 'Page'{
  Step @((Tap 'Left'),(ReadField 'Journal Menu' "$config._subList._selectedIndex"))
  if($Count -gt 0){ Step ((@((Tap $Key))*$Count)+@((ReadField 'Journal Menu' "$config._subList.selectedEntry.text"))) $Expect }
  Step @((Tap 'Accept'),$wait,(ReadField 'Journal Menu' "$config._optionsList._entryList.0.text"))
 }
 'Keys'{ Step ((@((Tap $Key))*$Count)+@((ReadField 'Journal Menu' "$config._subList.selectedEntry.text"),(ReadField 'Journal Menu' "$config._subList._selectedIndex"))) $Expect }
 'Open'{ Step @((Tap 'Accept'),$wait,(ReadField 'Journal Menu' "$config._optionsList._entryList.0.text"),(ReadField 'Journal Menu' "$config._optionsList._selectedIndex")) $Expect }
 'Options'{ Step @((Cmd 'gfx.dump' @{menu='Journal Menu';path="$config._optionsList._entryList";depth=2;max=120}),(ReadField 'Journal Menu' "$config._optionsList._selectedIndex")) }
 'Nav'{ Step ((@((Tap $Key))*$Count)+@((ReadField 'Journal Menu' "$config._optionsList._selectedIndex"),(ReadField 'Journal Menu' "$config._optionsList.selectedEntry.text"))) $Expect }
 'Accept'{ Step @((Tap 'Accept'),$wait,(ReadField 'Journal Menu' "$config._optionsList._selectedIndex"),(ReadField 'Journal Menu' "$config._optionsList.selectedEntry.text")) }
 'Read'{ Step @((ReadField $Menu $Path)) $Expect }
 'Dump'{ Step @((Cmd 'gfx.dump' @{menu=$Menu;path=$Path;depth=2;max=120})) }
 # Focus the page list and walk it until the page named by -Expect (default
 # 'Main') is selected: the list can open with no selection (-1), where a blind
 # Up wraps to the last page (launch 1b landed on 'Debug Mode').
 'Begin'{
  if(-not $Expect){$Expect='Main'}
  Step @((Tap 'Left'),(ReadField 'Journal Menu' "$config._subList._selectedIndex"))
  $tries=0
  do{
   $out=& $py "$root\audit\menupilot.py" send (ReadField 'Journal Menu' "$config._subList.selectedEntry.text") (ReadField 'Journal Menu' "$config._subList._selectedIndex") --timeout 25
   $out|Select-String 'RESULT'|ForEach-Object Line
   $text=($out -join "`n")
   if($text.Contains('value="'+$Expect+'"')){break}
   $key= if($text -match '_selectedIndex" type="number" value="-1"'){'Down'}else{'Up'}
   & $py "$root\audit\menupilot.py" send (Tap $key) $wait --timeout 25 | Select-String 'RESULT'|ForEach-Object Line
   $tries++
  }while($tries -lt 12)
  if($tries -ge 12){throw "Could not select page $Expect"}
  Step @((Tap 'Accept'),$wait,(ReadField 'Journal Menu' "$config._optionsList._entryList.0.text")) 'Begin Your Adventure'
  Step @((Tap 'Right'),(ReadField 'Journal Menu' "$config._optionsList._selectedIndex")) '0'
  Step @((Tap 'Accept'))
 }
 # Tween Menu -> Right -> Accept opens the inventory; dump the item list, close.
 'Inventory'{
  Step @((Tap 'Tween'),(Cmd 'wait' @{ms=1200}),(Tap 'Right'),(Cmd 'wait' @{ms=600}),(Tap 'Accept'),(Cmd 'wait' @{ms=2000}),(Cmd 'menu.list'))
  Step @((Cmd 'gfx.dump' @{menu='InventoryMenu';path='_root.Menu_mc.inventoryLists.itemList._entryList';depth=1;max=200}))
  Step @((Tap 'Cancel'),$wait,(Tap 'Cancel'),$wait,(Cmd 'menu.list'))
 }
 'Ping'{ Step @((Cmd 'ping'),(Cmd 'menu.list')) }
 'Quit'{
  Step @((Tap 'Journal'),$wait,(InvokeField 'Journal Menu' "$journal.SystemTab.onPress"),(InvokeField 'Journal Menu' "$journal.SystemTab.onRelease"),(ReadField 'Journal Menu' "$page.CategoryList_mc.List_mc.iSelectedIndex"))
  Step ((@((Tap 'Down'))*9)+@((ReadField 'Journal Menu' "$page.CategoryList_mc.List_mc.selectedEntry.text"))) '$QUIT'
  Step @((Tap 'Accept'),$wait,(ReadField 'Journal Menu' "$page.PCQuitList.iSelectedIndex")) '-1'
  Step @((Tap 'Down'),(Tap 'Down'),(ReadField 'Journal Menu' "$page.PCQuitList.selectedEntry.text")) '$Desktop'
  Step @((Tap 'Accept'),$wait,(ReadField 'Journal Menu' "$page.ConfirmPanel.ConfirmText.textField.text")) 'Quit to desktop?  Any unsaved progress will be lost.'
  & $py "$root\audit\menupilot.py" send (Tap 'Accept') --timeout 10 | Select-String 'RESULT|BATCH_DONE' | ForEach-Object Line
  exit 0
 }
}
