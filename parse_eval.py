import re

with open('eval_results.json', 'r') as f:
    text = f.read()

questions = re.split(r'--- Q\d+ ---', text)[1:]
for i, q in enumerate(questions, 1):
    q_text_match = re.search(r'Question:\s*(.*?)\s*Expected Route', q, re.DOTALL)
    ans_match = re.search(r'Sample Answer:\s*(.*?)(?=\n--- Q|\n\[\*\] Evaluation|\Z)', q, re.DOTALL)
    
    # Actually I just need the full answers. In eval_results.json, the answers are TRUNCATED!
    # Ah, I wrote `print(f"Sample Answer: {answer[:100]}...")` in run_eval.py.
