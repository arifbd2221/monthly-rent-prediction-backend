import json
import uuid
from datetime import datetime, UTC

from fastapi import Request
from starlette.responses import StreamingResponse
from database import get_db
from database import APILogDB


def write_log(req: Request, res: StreamingResponse, req_body: dict, res_body: str, process_time: float):

    db_gen = get_db()
    db = next(db_gen)
    token = "N/A"

    auth_header = req.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        # Extract the token part
        token = auth_header.split(" ")[1]

    try:
        res_body = json.loads(res_body)
    except Exception:
        res_body = None

    log = APILogDB(
        input_data=req_body,
        token=token,
        prediction="N/A",
        process_time=process_time,
        created_at=datetime.now(UTC)
    )
    db.add(log)
    db.commit()

    db.close()