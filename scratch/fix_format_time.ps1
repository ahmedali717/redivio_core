$path = "c:\Users\ahmed.ali\.gemini\antigravity\scratch\redivio_core\redivio_project\static\js\main.js"
$content = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)

# The end is currently corrupted:
# return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }
#    }
# }).mount('#app');

$target = "formatTime(isoString) {"
$index = $content.LastIndexOf($target)

if ($index -ge 0) {
    $correctEnd = @"
        formatTime(isoString) {
            if (!isoString) return '--:--';
            const date = new Date(isoString);
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
    }
}).mount('#app');
"@
    $newContent = $content.Substring(0, $index) + $correctEnd
    [System.IO.File]::WriteAllText($path, $newContent, [System.Text.Encoding]::UTF8)
    Write-Host "Fixed formatTime and end structure"
}
