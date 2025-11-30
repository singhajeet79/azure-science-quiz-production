import logging
import azure.functions as func
import os, json, uuid
from datetime import datetime
from azure.data.tables import TableClient
from typing import Dict, Any

TABLE_NAME = os.getenv("AZURE_TABLE_NAME", "QuizResponses")
CONNECTION_STRING = os.getenv("AZURE_TABLE_CONN", "")

# 🔥 Master Answer Key (using lowercase letters a, b, c, d)
CORRECT = ["c", "a", "b", "d", "a", "c", "b", "d", "a", "c"] 

# Map the frontend numeric index (0, 1, 2, 3) to the letter key (a, b, c, d)
INDEX_TO_LETTER = {
    "0": "a",
    "1": "b",
    "2": "c",
    "3": "d"
}

def normalize_answers(answers):
    """
    Converts student submission into an ordered list of letter answers (a, b, c, d).
    Handles both dict (q1:c) and list (0, 2, 1, null) formats.
    """
    out = []
    
    if isinstance(answers, dict):
        # Handles the old format (q1: c, q2: a, ...)
        for i in range(1, 11): 
            out.append(answers.get(f"q{i}", "").lower())
    
    elif isinstance(answers, list):
        # Handles the current frontend format (0, 2, 1, null, ...)
        for answer_index in answers:
            if answer_index is None:
                # Append an empty string or None for unattempted questions
                out.append(None)
            else:
                # Map the string index ("0", "1", "2") to the letter key ("a", "b", "c")
                # and convert to lowercase for comparison.
                mapped_answer = INDEX_TO_LETTER.get(str(answer_index), '')
                out.append(mapped_answer.lower())
    
    return out

def score_answers(student_ans, correct_ans):
    score = 0
    for s, c in zip(student_ans, correct_ans):
        # Need to handle None submissions from normalize_answers
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
    # Answers is now a list of strings/nulls from the frontend
    answers = body.get("answers", []) 

    # 🔥 Normalize structure: Maps ["0", "2", ...] to ["a", "c", ...]
    answers_list = normalize_answers(answers)

    # 🔥 Score
    score = score_answers(answers_list, CORRECT)

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
            "answers": json.dumps(answers_list), # Stores the final letter answers
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
