$path = "c:\Users\ahmed.ali\.gemini\antigravity\scratch\redivio_core\redivio_project\static\js\main.js"
$content = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::UTF8)

# Fix target 1
$target1 = "} catch (e) { this.showToast(`"Error`", 'error'); }`r`n            },"
$replacement1 = "} catch (e) { this.showToast(`"Error`", 'error'); }`r`n            }`r`n        },"

if ($content.Contains($target1)) {
    $content = $content.Replace($target1, $replacement1)
    Write-Host "Fixed target 1"
} else {
    # Try unix line endings
    $target1_u = "} catch (e) { this.showToast(`"Error`", 'error'); }`n            },"
    $replacement1_u = "} catch (e) { this.showToast(`"Error`", 'error'); }`n            }`n        },"
    if ($content.Contains($target1_u)) {
        $content = $content.Replace($target1_u, $replacement1_u)
        Write-Host "Fixed target 1 (unix)"
    } else {
        Write-Host "Could not find target 1"
    }
}

# Fix target 2
$target2 = "        }`r`n        },`r`n`r`n    },"
$replacement2 = "        },"

if ($content.Contains($target2)) {
    $content = $content.Replace($target2, $replacement2)
    Write-Host "Fixed target 2"
} else {
    $target2_u = "        }`n        },`n`n    },"
    $replacement2_u = "        },"
    if ($content.Contains($target2_u)) {
        $content = $content.Replace($target2_u, $replacement2_u)
        Write-Host "Fixed target 2 (unix)"
    } else {
        Write-Host "Could not find target 2"
    }
}

[System.IO.File]::WriteAllText($path, $content, [System.Text.Encoding]::UTF8)
