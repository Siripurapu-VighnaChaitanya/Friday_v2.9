param(
    [string]$CallType = "voice"   # "voice" or "video"
)

Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$uia = [System.Windows.Automation.AutomationElement]::RootElement

# Find WhatsApp window
$wa_cond = New-Object System.Windows.Automation.PropertyCondition(
    [System.Windows.Automation.AutomationElement]::NameProperty, 'WhatsApp')
$wa_win = $uia.FindFirst([System.Windows.Automation.TreeScope]::Children, $wa_cond)

if (-not $wa_win) {
    Write-Error "WhatsApp window not found"
    exit 1
}

# Determine button name to look for
# WhatsApp Desktop uses "Voice call" and "Video call" as accessibility names
$btnName = if ($CallType -eq "video") { "Video call" } else { "Voice call" }

# Search the full accessibility tree for the button by name
$btn_cond = New-Object System.Windows.Automation.PropertyCondition(
    [System.Windows.Automation.AutomationElement]::NameProperty, $btnName)
$btn = $wa_win.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $btn_cond)

if ($btn) {
    Write-Output "Found button: $btnName"
    # Invoke (click) the button via the InvokePattern
    try {
        $pattern = $btn.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
        $pattern.Invoke()
        Write-Output "SUCCESS: $btnName initiated"
        exit 0
    } catch {
        # Fallback: use Click() via legacy pattern
        try {
            $legacy = $btn.GetCurrentPattern([System.Windows.Automation.LegacyIAccessiblePattern]::Pattern)
            $legacy.DoDefaultAction()
            Write-Output "SUCCESS (legacy): $btnName initiated"
            exit 0
        } catch {
            Write-Error "Could not invoke button: $_"
            exit 2
        }
    }
} else {
    # Button not found - list all found buttons so we can debug the name
    Write-Output "Button '$btnName' not found. Available buttons:"
    $allEls = $wa_win.FindAll(
        [System.Windows.Automation.TreeScope]::Descendants,
        [System.Windows.Automation.Condition]::TrueCondition)
    foreach ($el in $allEls) {
        try {
            if ($el.Current.ControlType.ProgrammaticName -eq "ControlType.Button") {
                Write-Output ("  [" + $el.Current.Name + "]")
            }
        } catch {}
    }
    exit 3
}
