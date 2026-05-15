"""
Fix ai_service.py:
1. Add closing '"""' at indent=0 after line 330 (end of CONSENSUS_INSPECTION string content)
2. This properly closes INSPECTION_METHOD_COMPARE_PROMPT at its original location
"""
with open('c:/Users/dell/WorkBuddy/Claw/backend/services/ai_service.py', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line that has: "    '- 只输出 JSON，不要输出其他内容"""\n"
# This is the line where CONSENSUS_INSPECTION closes (with content before """)
# We need to insert a proper closing '"""' at indent=0 BEFORE this line
target_old = "    '- 只输出 JSON，不要输出其他内容\"\"\"\n'\n'\n'\n'# ============================================================\n'# 多参考共识感知审查 Prompt - 通用标准\n'# ============================================================\n'CONSENSUS_GENERAL_COMPARE_PROMPT = \"\"\"你是一位资深的国家标准审查专家。"

target_new = "    '- 只输出 JSON，不要输出其他内容\"\"\"\n'\n'    '\"\"\"\n'\n'\n'# ============================================================\n'# 多参考共识感知审查 Prompt - 通用标准\n'# ============================================================\n'CONSENSUS_GENERAL_COMPARE_PROMPT = \"\"\"你是一位资深的国家标准审查专家。"

# Do the replacement
idx = None
for i in range(len(lines) - 20):
    if ('CONSENSUS_GENERAL_COMPARE_PROMPT' in lines[i] and 
        lines[i-6].strip() == "- 只输出 JSON，不要输出其他内容\"\""):
        idx = i - 5
        print(f"Found at lines {i-5} to {i}")
        print(f"  Line {i-5}: {repr(lines[i-5][:50])}")
        print(f"  Line {i}: {repr(lines[i][:60])}")
        break

if idx:
    # Insert closing """ at idx, shifting everything after
    new_lines = lines[:idx] + ['    """\n', '\n', '\n'] + lines[idx:]
    with open('c:/Users/dell/WorkBuddy/Claw/backend/services/ai_service.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f"Fixed! Added closing '\"\"\"' at line {idx+1}")
    # Verify
    import ast
    with open('c:/Users/dell/WorkBuddy/Claw/backend/services/ai_service.py', encoding='utf-8') as f:
        content = f.read()
    try:
        ast.parse(content)
        print("Syntax OK!")
    except SyntaxError as e:
        print(f"Still has error at line {e.lineno}: {e.msg}")
else:
    print("Could not find target location")