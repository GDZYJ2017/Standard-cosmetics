with open('c:/Users/dell/WorkBuddy/Claw/backend/services/ai_service.py', encoding='utf-8') as f:
    lines = f.readlines()

print('--- Lines 285-342 (raw) ---')
for i in range(284, 342):
    line = lines[i]
    print(f'LINE {i+1}: {repr(line)}')