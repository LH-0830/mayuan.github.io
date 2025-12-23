import re
import json
import os

# 定义文件名与单元名称的映射
FILES_MAPPING = {
    "一.docx.txt": "第一单元",
    "二.docx.txt": "第二单元",
    "三.docx.txt": "第三单元",
    "四.docx.txt": "第四单元",
    "五.docx.txt": "第五单元",
    "六.docx.txt": "第六单元"
}

def parse_doc_content(raw_text):
    # 1. 移除 标签
    text = re.sub(r'\\', '', raw_text)
    
    # 2. 分离题目和答案区域
    # 寻找文末答案区的特征 (例如 "1-5:" 或 "81:")
    lines = text.split('\n')
    q_lines = []
    a_lines = []
    is_answer_section = False
    
    for line in lines:
        line = line.strip()
        # 特征：以数字开头，后面跟冒号或范围，且包含ABCD或对错
        if (re.match(r'^\d+[-:]', line) or re.match(r'^\d+\s*:', line)) and any(c in line for c in ['A','B','C','D','对','错']):
            is_answer_section = True
        
        if is_answer_section:
            a_lines.append(line)
        else:
            q_lines.append(line)
            
    # 3. 解析答案 Map
    ans_text = "\n".join(a_lines)
    ans_map = {}
    
    # 解析 "1-5: A B C"
    for match in re.finditer(r'(\d+)-(\d+)[:：]\s*(.*?)(?=\s\d+-|\n|$)', ans_text):
        start, end = int(match.group(1)), int(match.group(2))
        answers = match.group(3).split()
        curr = start
        for a in answers:
            if curr <= end:
                ans_map[curr] = normalize_ans(a)
                curr += 1
                
    # 解析 "81. ABCD"
    for match in re.finditer(r'(\d+)[\.:：\s]+([A-Za-z]+)', ans_text):
        ans_map[int(match.group(1))] = normalize_ans(match.group(2))

    # 4. 解析题目
    questions = []
    q_text = "\n".join(q_lines)
    current_q = None
    
    for line in q_text.split('\n'):
        line = line.strip()
        if not line: continue
        
        # 识别新题目 "1. (单选题)..."
        match = re.match(r'^(\d+)[\.\、]\s*(.*)', line)
        if match:
            if current_q: questions.append(current_q)
            qid = int(match.group(1))
            content = match.group(2)
            
            # 简单判断题型
            qtype = "单选题"
            if "判断" in content: qtype = "判断题"
            elif "多选" in content: qtype = "多选题"
            
            current_q = {
                "id": qid,
                "type": qtype,
                "question": content,
                "options": [],
                "answer": ans_map.get(qid, "")
            }
        elif current_q:
            if re.match(r'^[A-Z][\.\、]', line):
                current_q['options'].append(line)
            else:
                if not current_q['options']:
                    current_q['question'] += line
                    
    if current_q: questions.append(current_q)
    return questions

def normalize_ans(ans):
    ans = ans.replace("对", "A").replace("错", "B")
    return "".join(sorted(ans.upper()))

# 主程序：读取文件并生成 JS
all_data = {}

# 模拟读取文件过程 (在实际使用时，请确保你的docx转成的txt或内容在同级目录)
# 这里为了让你直接运行，你需要把那6个文件的内容准备好，或者让脚本去读文件
# 假设你已经有了6个文本文件，或者你可以将之前的 RAW_TEXT_DATA 替换为文件读取

print("开始生成数据文件...")
for filename, unit_name in FILES_MAPPING.items():
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"正在处理: {unit_name}...")
            all_data[unit_name] = parse_doc_content(content)
    else:
        print(f"⚠️ 未找到文件: {filename}，跳过。")

# 生成 JavaScript 文件
js_content = f"const QUIZ_DATA = {json.dumps(all_data, ensure_ascii=False, indent=2)};"

with open('quiz_data.js', 'w', encoding='utf-8') as f:
    f.write(js_content)

print("✅ 成功生成 quiz_data.js！")