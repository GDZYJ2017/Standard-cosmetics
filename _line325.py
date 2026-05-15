with open('c:/Users/dell/WorkBuddy/Claw/backend/services/ai_service.py', 'rb') as f:
    content = f.read()
lines = content.split(b'\n')
print(f'Total lines: {len(lines)}')
print()
for i in range(324, 340):
    raw = lines[i]
    print(f'Line {i+1}: {raw}')