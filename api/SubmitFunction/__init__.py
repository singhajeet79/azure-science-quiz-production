import logging
import azure.functions as func
import os, json, uuid
from datetime import datetime
from azure.data.tables import TableClient
from typing import Dict, Any

TABLE_NAME = os.getenv("AZURE_TABLE_NAME", "QuizResponses")
CONNECTION_STRING = os.getenv("AZURE_TABLE_CONN", "")

# 🔥 Move correct answers into environment variable or embed here
CORRECT = ["c", "a", "b", "d", "a", "c", "b", "d", "a", "c"]  # <-- REPLACE WITH YOUR REAL ANSWERS

def normalize_answers(answers):
    """
    Convert dict → ordered list of answers.
    Expected keys: q1, q2, ... q10
    """
    if isinstance(answers, dict):
        out = []
        for i in range(1, 11):  # 10 questions
            out.append(answers.get(f"q{i}", "").lower())
        return out
    elif isinstance(answers, list):
        return [str(a).lower() for a in answers]
    else:
        return []

def score_answers(student_ans, correct_ans):
    score = 0
    for s, c in zip(student_ans, correct_ans):
        if s == c:
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
    answers = body.get("answers", {})

    # 🔥 Normalize structure before scoring
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
