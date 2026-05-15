with open('c:/Users/dell/WorkBuddy/Claw/backend/services/ai_service.py', encoding='utf-8') as f:
    lines = f.readlines()
print(f'Total lines: {len(lines)}')
print()
print('--- lines 282-292 ---')
for i in range(282, 292):
    stripped = lines[i].rstrip()
    indent = len(lines[i]) - len(lines[i].lstrip())
    content = repr(stripped[:80] if stripped else '(empty)')
    print(f'LINE {i+1}: indent={indent} {content}')
print()
print('--- lines 360-372 ---')
for i in range(360, 372):
    stripped = lines[i].rstrip()
    indent = len(lines[i]) - len(lines[i].lstrip())
    content = repr(stripped[:80] if stripped else '(empty)')
    print(f'LINE {i+1}: indent={indent} {content}')
print()
print('--- lines 560-590 ---')
for i in range(560, 590):
    stripped = lines[i].rstrip()
    indent = len(lines[i]) - len(lines[i].lstrip())
    content = repr(stripped[:80] if stripped else '(empty)')
    print(f'LINE {i+1}: indent={indent} {content}')