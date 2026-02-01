from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db import get_connection
from typing import Optional
from fastapi import Depends
from app.auth.dependencies import require_student, require_admin, get_current_user

router = APIRouter()

class ActivityRequestCreate(BaseModel):
    activity_id: str

#EndPoint #2. Creating activity request
@router.post("/")
def create_activity_request(req: ActivityRequestCreate, student=Depends(require_student)):
    
    try:
        conn = get_connection()
        cur = conn.cursor()

        student_id = student["user_id"]

        cur.execute(
            """
            INSERT INTO activity_requests(student_id, activity_id)
            VALUES (%s, %s)
            RETURNING id;
            """,
            (student_id, req.activity_id)
        )
        
        request_id = cur.fetchone()[0]
        conn.commit()

        cur.close()
        conn.close()

        return{
            "request_id": request_id,
            "status": "pending",
            "message": "Activity request Submitted"
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

#EndPoint #3. Handling approval of activity  
class ActivityRequestApprove(BaseModel):
    admin_id: int

@router.put("/{request_id}/approve")
def approve_activity_request(request_id: int, data: ActivityRequestApprove,admin=Depends(require_admin)):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            UPDATE activity_requests
            SET status = 'approved',
                approved_at = CURRENT_TIMESTAMP,
                approved_by = %s
            WHERE id = %s
              AND status = 'pending'
            RETURNING id;
            """,
            (data.admin_id, request_id)
        )

        result = cur.fetchone()
        conn.commit()

        cur.close()
        conn.close()

        if result is None:
            raise HTTPException(
                status_code=404,
                detail="Request not found or already processed"
            )

        return {
            "request_id": request_id,
            "status": "approved",
            "message": "Activity request approved"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

#Segment 2: Admin Dashboard - Viewing all requests

@router.get("/")
def get_activity_requests(status: Optional[str] = None, admin=Depends(require_admin)):
    try:
        conn = get_connection()
        cur = conn.cursor()

        if status:
            cur.execute(
                """
                SELECT r.id, s.name, a.name, r.status, r.requested_at
                FROM activity_requests r
                JOIN students s ON r.student_id = s.id
                JOIN activities a ON r.activity_id = a.id
                WHERE r.status = %s
                ORDER BY r.requested_at DESC;
                """,
                (status,)
            )
        else:
            cur.execute(
                """
                SELECT r.id, s.name, a.name, r.status, r.requested_at
                FROM activity_requests r
                JOIN students s ON r.student_id = s.id
                JOIN activities a ON r.activity_id = a.id
                ORDER BY r.requested_at DESC;
                """
            )

        rows = cur.fetchall()
        cur.close()
        conn.close()

        return [
            {
                "request_id": r[0],
                "student_name": r[1],
                "activity_name": r[2],
                "status": r[3],
                "requested_at": r[4],
            }
            for r in rows
        ]

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me")
def get_my_activity_requests(user=Depends(require_student)):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT r.id, a.name, r.status, r.requested_at
        FROM activity_requests r
        JOIN activities a ON r.activity_id = a.id
        WHERE r.student_id = %s
        ORDER BY r.requested_at DESC;
        """,
        (user["user_id"],)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "request_id": r[0],
            "activity": r[1],
            "status": r[2],
            "requested_at": r[3]
        }
        for r in rows
    ]
