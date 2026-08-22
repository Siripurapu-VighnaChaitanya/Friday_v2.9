Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$uia = [System.Windows.Automation.AutomationElement]::RootElement

# Find WhatsApp window
$wa_cond = New-Object System.Windows.Automation.PropertyCondition(
    [System.Windows.Automation.AutomationElement]::NameProperty, 'WhatsApp')
$wa_win = $uia.FindFirst([System.Windows.Automation.TreeScope]::Children, $wa_cond)

if ($wa_win) {
    Write-Output "Found WhatsApp!"
    
    # Find all buttons in the tree and list their names
    $allEls = $wa_win.FindAll(
        [System.Windows.Automation.TreeScope]::Descendants,
        [System.Windows.Automation.Condition]::TrueCondition)
    
    foreach ($el in $allEls) {
        try {
            if ($el.Current.ControlType.ProgrammaticName -eq "ControlType.Button") {
                Write-Output ("BUTTON: [" + $el.Current.Name + "]")
            }
        } catch {}
    }
} else {
    Write-Output "WhatsApp NOT open"
}
