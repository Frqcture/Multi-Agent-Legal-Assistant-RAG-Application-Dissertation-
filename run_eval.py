import os
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"
TEST_USER = "eval_user"
TEST_PASS = "eval_pass"
TEST_DOCS_DIR = os.path.join("Backend", "TestDocuments")

# The 20 Test Queries from EVALUATION_TEST_PLAN.md
TEST_QUERIES = [
    # Fact-Retrieval (Responder)
    {"id": "Q1", "route": "Responder", "target_doc": "Thompson_v_Meridian_Construction.pdf", "question": "What was the total contract price in the Thompson v Meridian Construction case?"},
    {"id": "Q2", "route": "Responder", "target_doc": "Williams_v_Ashford_Logistics_Employment.pdf", "question": "On what date was Sarah Williams dismissed from her position?"},
    {"id": "Q3", "route": "Responder", "target_doc": "Chen_Estate_Probate.pdf", "question": "Who are the named beneficiaries in Robert Chen's will?"},
    {"id": "Q4", "route": "Responder", "target_doc": "DataFlow_v_NexGen_IP_Dispute.pdf", "question": "What is the UK patent number at issue in the DataFlow v NexGen dispute?"},
    {"id": "Q5", "route": "Responder", "target_doc": "Patel_Tenancy_Dispute.pdf", "question": "What is the monthly rent in the Patel tenancy agreement?"},
    {"id": "Q6", "route": "Responder", "target_doc": "Thompson_v_Meridian_Construction.pdf", "question": "What defects were identified in the Thompson construction project?"},
    {"id": "Q7", "route": "Responder", "target_doc": "Williams_v_Ashford_Logistics_Employment.pdf", "question": "How long was Sarah Williams employed before her dismissal?"},
    {"id": "Q8", "route": "Responder", "target_doc": "Chen_Estate_Probate.pdf", "question": "What is the total net value of the Chen estate?"},
    {"id": "Q9", "route": "Responder", "target_doc": "DataFlow_v_NexGen_IP_Dispute.pdf", "question": "What specific trade secrets does DataFlow allege NexGen misappropriated?"},
    {"id": "Q10", "route": "Responder", "target_doc": "Patel_Tenancy_Dispute.pdf", "question": "What repairs were requested by the Patel family?"},
    
    # Document Drafting (Drafter)
    {"id": "Q11", "route": "Drafter", "target_doc": "Thompson_v_Meridian_Construction.pdf", "question": "Draft a letter before action for the Thompson v Meridian construction dispute"},
    {"id": "Q12", "route": "Drafter", "target_doc": "Williams_v_Ashford_Logistics_Employment.pdf", "question": "Draft a witness statement for Sarah Williams' employment tribunal claim"},
    {"id": "Q13", "route": "Drafter", "target_doc": "Chen_Estate_Probate.pdf", "question": "Draft a grant of probate application cover letter for the Chen estate"},
    {"id": "Q14", "route": "Drafter", "target_doc": "DataFlow_v_NexGen_IP_Dispute.pdf", "question": "Draft a cease and desist letter for the DataFlow v NexGen IP dispute"},
    {"id": "Q15", "route": "Drafter", "target_doc": "Patel_Tenancy_Dispute.pdf", "question": "Draft a Section 11 disrepair claim letter for the Patel tenancy case"},
    {"id": "Q16", "route": "Drafter", "target_doc": "Thompson_v_Meridian_Construction.pdf", "question": "Draft a settlement proposal letter for the Thompson construction case"},
    {"id": "Q17", "route": "Drafter", "target_doc": "Williams_v_Ashford_Logistics_Employment.pdf", "question": "Draft the grounds of complaint for Sarah Williams' unfair dismissal ET1 form"},
    {"id": "Q18", "route": "Drafter", "target_doc": "Chen_Estate_Probate.pdf", "question": "Draft a beneficiary notification letter for the Chen estate"},
    {"id": "Q19", "route": "Drafter", "target_doc": "DataFlow_v_NexGen_IP_Dispute.pdf", "question": "Draft a licensing agreement proposal for the DataFlow IP matter"},
    {"id": "Q20", "route": "Drafter", "target_doc": "Patel_Tenancy_Dispute.pdf", "question": "Draft a tenancy deposit return demand letter for the Patel case"}
]

def setup_session():
    print("[*] Setting up authenticated session...")
    session = requests.Session()
    
    # Try to register
    reg_res = session.post(f"{BASE_URL}/register", data={"username": TEST_USER, "password": TEST_PASS})
    if reg_res.status_code == 200:
        print("    -> Registered new eval_user")
    elif reg_res.status_code == 400 and "Username already exists" in reg_res.text:
        print("    -> User already exists")
    else:
        print(f"    -> Register failed: {reg_res.text}")
        
    # Login
    login_res = session.post(f"{BASE_URL}/login", data={"username": TEST_USER, "password": TEST_PASS})
    if login_res.status_code != 200:
        print(f"[-] Login failed: {login_res.text}")
        exit(1)
        
    print("    -> Logged in successfully!")
    
    # Extract CSRF token and set it in the headers for all future requests
    if 'csrf_token' in session.cookies:
        session.headers.update({"x-csrf-token": session.cookies.get('csrf_token')})
        
    return session

def cleanup_files(session):
    print("\n[*] Cleaning up any existing documents...")
    res = session.get(f"{BASE_URL}/files")
    if res.status_code == 200:
        files = res.json().get("files", [])
        if not files:
            print("    -> Workspace is clear. No files to delete.")
        for f in files:
            file_name = f['name'] if isinstance(f, dict) else f
            del_res = session.delete(f"{BASE_URL}/files/{file_name}")
            print(f"    -> Deleted: {file_name} [{del_res.status_code}]")
    else:
        print(f"[-] Failed to fetch files for cleanup: {res.text}")

def upload_documents(session):
    print(f"\n[*] Uploading test documents from {TEST_DOCS_DIR} ...")
    if not os.path.exists(TEST_DOCS_DIR):
        print(f"[-] Missing directory: {TEST_DOCS_DIR}")
        exit(1)
        
    files_to_upload = []
    file_handles = []
    
    try:
        for file_name in os.listdir(TEST_DOCS_DIR):
            if file_name.endswith('.pdf'):
                file_path = os.path.join(TEST_DOCS_DIR, file_name)
                fh = open(file_path, 'rb')
                file_handles.append(fh)
                files_to_upload.append(('files', (file_name, fh, 'application/pdf')))
                
        if not files_to_upload:
            print("    -> No PDFs found in TestDocuments!")
            return
            
        res = session.post(f"{BASE_URL}/upload", files=files_to_upload)
        if res.status_code == 200:
            print(f"    -> Successfully uploaded {len(files_to_upload)} files!")
        else:
            print(f"[-] Upload failed: {res.text}")
    finally:
        for fh in file_handles:
            fh.close()
            
    print("    -> Giving Chroma DB 5 seconds to settle...")
    time.sleep(5)

def run_evaluation(session):
    print("\n[*] Running Evaluation Queries...")
    results = []
    
    for q in TEST_QUERIES:
        print(f"\n--- {q['id']} ---")
        print(f"Question: {q['question']}")
        
        req_start = time.time()
        res = session.post(f"{BASE_URL}/ask", json={"question": q['question']})
        req_end = time.time()
        
        if res.status_code != 200:
            print(f"[-] Query failed: {res.text}")
            continue
            
        data = res.json()
        answer = data.get("answer", "")
        steps = data.get("steps", [])
        
        # Determine Routing
        route_taken = "Unknown"
        agent_names = [step.get("agent") for step in steps]
        if "Responder" in agent_names:
            route_taken = "Responder"
        elif "Document Drafter" in agent_names:
            route_taken = "Drafter"
            
        routing_correct = (route_taken == q['route'])
        
        # Check retrieval success
        retrieval_success = False
        chunks_retrieved = []
        for step in steps:
            # We are looking for the step where 'retrieval' or similar happened in the coordinator logs
            # Actually, the chunks retrieved might not be natively exposed unless the backend logs it cleanly.
            if "content" in step and q['target_doc'] in step["content"]:
                retrieval_success = True
                break
                
        # Wait, if step["agent"] is coordinator / worker and contains document names
        # Let's just do a naive check if the target document was referenced in the trace
        target_doc = q['target_doc']
        doc_mentioned_in_trace = any(target_doc in step.get("content", "") for step in steps)
        # Check if the document was cited inside the final answer
        doc_cited_in_answer = target_doc in answer
            
        print(f"    Expected Route: {q['route']} | Taken: {route_taken} | Correct? {routing_correct}")
        print(f"    Target Document Cited in Answer/Trace? {doc_mentioned_in_trace or doc_cited_in_answer}")
        print(f"    Time taken: {req_end - req_start:.2f}s")
        print(f"    Sample Answer: {answer[:100]}...")
        
        results.append({
            "id": q["id"],
            "route_correct": routing_correct,
            "target_cited": doc_mentioned_in_trace or doc_cited_in_answer,
            "time_taken": req_end - req_start,
            "answer": answer
        })
        
    print("\n[*] Evaluation Summary")
    correct_routes = sum(1 for r in results if r["route_correct"])
    targets_cited = sum(1 for r in results if r["target_cited"])
    
    print(f"    Route Accuracy: {correct_routes}/{len(results)} ({(correct_routes/len(results))*100:.1f}%)")
    print(f"    Retrieval Target Ref Usage: {targets_cited}/{len(results)} ({(targets_cited/len(results))*100:.1f}%)")

if __name__ == "__main__":
    s = setup_session()
    cleanup_files(s)
    upload_documents(s)
    run_evaluation(s)
    print("\n[*] Done!")
