$path = "c:\Users\ahmed.ali\.gemini\antigravity\scratch\redivio_core\redivio_project\static\js\main.js"
$content = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)

# The end of the file currently looks like:
#         formatTime(isoString) { ... },
#
#     mounted() { ... }
# }).mount('#app');

# I want it to be:
#         formatTime(isoString) { ... }
#     }
# }).mount('#app');

# Let's find the position of formatTime and clean up after it
$target = "formatTime(isoString) {"
$index = $content.LastIndexOf($target)

if ($index -ge 0) {
    # Find the closing brace of formatTime
    $afterFormatTime = $content.Substring($index)
    $closingBraceIndex = $afterFormatTime.IndexOf("}")
    
    if ($closingBraceIndex -ge 0) {
        $cleanContent = $content.Substring(0, $index + $closingBraceIndex + 1)
        $cleanContent += "`r`n    }`r`n}).mount('#app');"
        [System.IO.File]::WriteAllText($path, $cleanContent, [System.Text.Encoding]::UTF8)
        Write-Host "Cleaned up the end of the file"
    }
} else {
    Write-Host "Could not find formatTime"
}
