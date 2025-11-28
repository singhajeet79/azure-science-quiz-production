import logging
import azure.functions as func
import os, json, uuid
from datetime import datetime
from azure.data.tables import TableClient
from typing import Dict, Any

# Table name (create a table named 'QuizResponses' in your storage account)
TABLE_NAME = os.getenv("AZURE_TABLE_NAME", "QuizResponses")
# Connection string should be set in Function App settings (do NOT hardcode)
CONNECTION_STRING = os.getenv("AZURE_TABLE_CONN", "")

def score_answers(answers, correct):
    score = 0
    for i in range(min(len(answers), len(correct))):
        if answers[i] is not None and answers[i] == correct[i]:
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
    answers = body.get("answers", [])

    # Load correct answers from a small embedded file in Function app (questions.json)
    try:
        func_dir = os.path.dirname(__file__)
        qpath = os.path.join(func_dir, "..", "..", "frontend", "questions.json")
        with open(qpath, "r") as fh:
            qdata = json.load(fh)
        correct = qdata.get("answers", [])
    except Exception as e:
        logging.warning("Could not load questions for scoring: %s", e)
        correct = []

    score = score_answers(answers, correct)

    attempt_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()

    # Store result in Table Storage
    try:
        table_client = TableClient.from_connection_string(CONNECTION_STRING, table_name=TABLE_NAME)
        entity = {
            "PartitionKey": school or "unknown",
            "RowKey": attempt_id,
            "student": student or "unknown",
            "sessionToken": session_token,
            "timestamp": timestamp,
            "answers": json.dumps(answers),
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
