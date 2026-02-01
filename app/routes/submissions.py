from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db import get_connection
from typing import Optional
from fastapi import Depends
from app.auth.dependencies import require_admin,require_student, get_current_user

router = APIRouter()

class SubmissionCreate(BaseModel):
    request_id: int
    proof: str

#EndPoint #4. Creating submission 
@router.post("/")
def create_submission(data: SubmissionCreate, student=Depends(require_student)):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT id
            FROM activity_requests
            WHERE id = %s AND status = 'approved';
            """,
            (data.request_id,)
        )

        approved_request = cur.fetchone()
        if approved_request is None:
            raise HTTPException(
                status_code=400,
                detail="Activity request is not approved or does not exist"
            )

        cur.execute(
            """
            INSERT INTO submissions (request_id, proof)
            VALUES (%s, %s)
            RETURNING id;
            """,
            (data.request_id, data.proof)
        )

        submission_id = cur.fetchone()[0]
        conn.commit()

        cur.close()
        conn.close()

        return {
            "submission_id": submission_id,
            "status": "pending",
            "message": "Submission created successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class SubmissionVerify(BaseModel):
    admin_id: int


#EndPoint #5. Admin verifiying the submission
@router.put("/{submission_id}/verify")
def verify_submission(submission_id: int, data: SubmissionVerify, admin=Depends(require_admin)):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            UPDATE submissions
            SET status = 'approved',
                verified_by = %s,
                verified_at = CURRENT_TIMESTAMP
            WHERE id = %s
              AND status = 'pending'
            RETURNING id;
            """,
            (data.admin_id, submission_id)
        )

        result = cur.fetchone()
        conn.commit()

        cur.close()
        conn.close()

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Submission not found or already verified"
            )

        return {
            "submission_id": submission_id,
            "status": "approved",
            "message": "Submission verified successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


#Segment 2.2: Admin Viewing all submissions
@router.get("/")
def get_submissions(status: Optional[str] = None, admin=Depends(require_admin)):
    try:
        conn = get_connection()
        cur = conn.cursor()

        if status:
            cur.execute(
                """
                SELECT sub.id, s.name, a.name, sub.status, sub.submitted_at
                FROM submissions sub
                JOIN activity_requests r ON sub.request_id = r.id
                JOIN students s ON r.student_id = s.id
                JOIN activities a ON r.activity_id = a.id
                WHERE sub.status = %s
                ORDER BY sub.submitted_at DESC;
                """,
                (status,)
            )
        else:
            cur.execute(
                """
                SELECT sub.id, s.name, a.name, sub.status, sub.submitted_at
                FROM submissions sub
                JOIN activity_requests r ON sub.request_id = r.id
                JOIN students s ON r.student_id = s.id
                JOIN activities a ON r.activity_id = a.id
                ORDER BY sub.submitted_at DESC;
                """
            )

        rows = cur.fetchall()
        cur.close()
        conn.close()

        return [
            {
                "submission_id": r[0],
                "student_name": r[1],
                "activity_name": r[2],
                "status": r[3],
                "submitted_at": r[4],
            }
            for r in rows
        ]

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me")
def get_my_submissions(user=Depends(require_student)):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT s.id, a.name, s.status, s.submitted_at
        FROM submissions s
        JOIN activity_requests r ON s.request_id = r.id
        JOIN activities a ON r.activity_id = a.id
        WHERE r.student_id = %s
        ORDER BY s.submitted_at DESC;
        """,
        (user["user_id"],)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "submission_id": r[0],
            "activity": r[1],
            "status": r[2],
            "submitted_at": r[3]
        }
        for r in rows
    ]
