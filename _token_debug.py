import tokenize, io

with open('c:/Users/dell/WorkBuddy/Claw/backend/services/ai_service.py', encoding='utf-8') as f:
    src = f.read()

tokens = list(tokenize.generate_tokens(io.StringIO(src).readline))

# Find tokens in lines 285-375
print('Tokens in lines 285-375:')
for i, tok in enumerate(tokens):
    if 284 <= tok.start[0] <= 375:
        type_names = {1: 'STRING', 2: 'NUMBER', 3: 'STRING', 4: 'NAME', 5: 'NEWLINE',
                       54: 'COMMENT', 0: 'ENDMARKER', 51: 'INDENT', 52: 'DEDENT', 53: 'LPAR', 54: '...'}
        print(f'  Line {tok.start[0]:3d}({tok.start[1]:2d})-{tok.end[0]:3d}({tok.end[1]:2d}): type={tok.type} {repr(tok.string[:50] if tok.string else "")}')