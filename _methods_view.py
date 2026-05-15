with open('c:/Users/dell/WorkBuddy/Claw/backend/services/ai_service.py', encoding='utf-8') as f:
    lines = f.readlines()

# Find ALL class methods and module-level items
print('=== AIService class structure (methods at indent=4) ===')
for i, l in enumerate(lines):
    indent = len(l) - len(l.lstrip())
    if 'class AIService' in l:
        print(f'Line {i+1}: CLASS START {repr(l.strip()[:50])}')
    stripped = l.strip()
    if not stripped:
        continue
    if indent == 4 and (stripped.startswith('def ') or stripped.startswith('async def ') or stripped.startswith('"""') or 'PROMPT' in stripped):
        print(f'Line {i+1}: indent=4 {repr(stripped[:70])}')
    elif indent == 0 and ('PROMPT' in stripped or 'async def' in stripped or 'def ' in stripped or 'class ' in stripped):
        print(f'Line {i+1}: indent=0 (module) {repr(stripped[:70])}')

print('\n=== Key methods ===')
for i, l in enumerate(lines):
    stripped = l.strip()
    if not stripped:
        continue
    indent = len(l) - len(l.lstrip())
    for kw in ['compare_documents', 'compare_sections', '_compare_against_consensus', 'synthesize_multi_reference', 'close']:
        if kw in stripped and (stripped.startswith('def ') or stripped.startswith('async def ')):
            print(f'Line {i+1}: indent={indent} {repr(stripped[:70])}')