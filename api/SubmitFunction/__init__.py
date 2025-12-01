import logging
import azure.functions as func
import os, json, uuid
from datetime import datetime
from azure.data.tables import TableClient
from typing import Dict, Any

TABLE_NAME = os.getenv("AZURE_TABLE_NAME", "QuizResponses")
CONNECTION_STRING = os.getenv("AZURE_TABLE_CONN", "")

# 🔥 FIX: Use the numeric indices from your provided questions.json
# [1, 0, 0, 3, 1, 1, 3, 2, 2, 3] are the correct answer indices (0-3)
# Note: These values are stored as strings for comparison below.
CORRECT_ANSWERS_INDICES = ["1", "0", "0", "3", "1", "1", "3", "2", "2", "3"]

def normalize_answers(answers):
    """
    Converts student submission into an ordered list of string indices ("0", "1", etc.).
    This ensures consistency for scoring against CORRECT_ANSWERS_INDICES.
    """
    out = []
    
    # The frontend now sends 'answers' as a list of strings/nulls (e.g., ["0", "2", null, ...])
    if isinstance(answers, list):
        for answer_index in answers:
            if answer_index is None:
                # Append None for unattempted questions
                out.append(None)
            else:
                # Convert to string to match the format of CORRECT_ANSWERS_INDICES
                out.append(str(answer_index)) 
    
    # Fallback/Old Dictionary Format handler (left for robustness)
    elif isinstance(answers, dict):
        for i in range(1, 11): 
            # Takes value from "q1" and converts it to string
            val = answers.get(f"q{i}")
            out.append(str(val) if val is not None else None)
            
    return out

def score_answers(student_ans, correct_ans):
    score = 0
    # Both student_ans and correct_ans now contain string indices ("0", "1", ...) or None
    for s, c in zip(student_ans, correct_ans):
        # Strict comparison of string indices
        if s is not None and s == c:
            score += 1
    return score

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Processing quiz submission.")
    if not CONNECTION_STRING:
        return func.HttpResponse("Server misconfigured: missing AZURE_TABLE_CONN", status_code=500)

    try:
        body = req.get_json()
    except ValueError:
        return func.HttpResponse("Invalid JSON", status_code=400)

    session_token = body.get("sessionToken")
    student = body.get("student")
    school = body.get("school")
    # Answers is a list of strings/nulls from the frontend
    answers = body.get("answers", []) 

    # 🔥 Normalize structure: Ensures all answers are strings or None
    answers_list = normalize_answers(answers)

    # 🔥 Score: Comparison of string indices
    score = score_answers(answers_list, CORRECT_ANSWERS_INDICES)

    attempt_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()

    # Store
    try:
        table_client = TableClient.from_connection_string(CONNECTION_STRING, table_name=TABLE_NAME)
        entity = {
            "PartitionKey": school or "unknown",
            "RowKey": attempt_id,
            "student": student or "unknown",
            "sessionToken": session_token,
            "timestamp": timestamp,
            "answers": json.dumps(answers_list), 
            "score": score
        }
        table_client.create_entity(entity)
    except Exception as ex:
        logging.error("Failed to write to table: %s", ex)
        return func.HttpResponse("Failed to store result", status_code=500)

    return func.HttpResponse(
        json.dumps({"attemptId": attempt_id, "score": score}),
        mimetype="application/json",
        status_code=200
    )
