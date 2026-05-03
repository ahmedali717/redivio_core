import base64
import os

img_path = r'C:\Users\ahmed.ali\.gemini\antigravity\brain\3e4678c3-9403-4a4b-b3a2-3b52466fe619\restaurant_logo_placeholder_1777816083101.png'
with open(img_path, 'rb') as f:
    b64 = base64.b64encode(f.read()).decode('utf-8')

with open('logo_b64.txt', 'w') as f:
    f.write(b64)
