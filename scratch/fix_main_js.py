import os

path = r"c:\Users\ahmed.ali\.gemini\antigravity\scratch\redivio_core\redivio_project\static\js\main.js"

with open(path, 'rb') as f:
    content = f.read()

# 1. Fix the brace after addSaleGroup
# We look for the pattern around the toast message
target1 = b'} catch (e) { this.showToast("Error", \'error\'); }\r\n            },'
replacement1 = b'} catch (e) { this.showToast("Error", \'error\'); }\r\n            }\r\n        },'

if target1 in content:
    content = content.replace(target1, replacement1)
    print("Fixed target 1")
else:
    # Try with unix line endings just in case
    target1_u = b'} catch (e) { this.showToast("Error", \'error\'); }\n            },'
    replacement1_u = b'} catch (e) { this.showToast("Error", \'error\'); }\n            }\n        },'
    if target1_u in content:
        content = content.replace(target1_u, replacement1_u)
        print("Fixed target 1 (unix)")
    else:
        print("Could not find target 1")

# 2. Fix the extra braces at the end
target2 = b'        }\r\n        },\r\n\r\n    },'
replacement2 = b'        },\r\n'

if target2 in content:
    content = content.replace(target2, replacement2)
    print("Fixed target 2")
else:
    target2_u = b'        }\n        },\n\n    },'
    replacement2_u = b'        },\n'
    if target2_u in content:
        content = content.replace(target2_u, replacement2_u)
        print("Fixed target 2 (unix)")
    else:
        print("Could not find target 2")

with open(path, 'wb') as f:
    f.write(content)
