with open('c:/Users/dell/WorkBuddy/Claw/backend/services/ai_service.py', encoding='utf-8') as f:
    lines = f.readlines()
print(f'Total lines: {len(lines)}')
# Show key ranges
for start, end in [(326, 345), (358, 375), (620, 645)]:
    print(f'\n--- lines {start}-{end} ---')
    for i in range(start-1, end):
        stripped = lines[i].rstrip()
        indent = len(lines[i]) - len(lines[i].lstrip())
        content = stripped[:85] if stripped else '(empty)'
        print(f'LINE {i+1}: indent={indent} {repr(content)}')