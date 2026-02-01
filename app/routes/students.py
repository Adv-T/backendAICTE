from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.db import get_connection
from fastapi import Depends
from app.auth.dependencies import require_admin, require_student, get_current_user

router = APIRouter()


class StudentCreate(BaseModel):
    name: str
    usn: str
    email: str

"""
@router.post("/")
def create_student(student: StudentCreate):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            
            INSERT INTO students(name, usn, email)
            VALUES (%s, %s, %s)
            RETURNING id;
            ,
            (student.name, student.usn, student.email)
        )

        student_id = cur.fetchone()[0]
        conn.commit()

        cur.close()
        conn.close()

        return {"id": student_id, "message": "Student created"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
"""
        

@router.get("/{student_id}/points")
def get_student_points(student_id: int, user=Depends(get_current_user)):
    if user["role"] == "student" and user["user_id"] != student_id:
        raise HTTPException(status_code=403, detail="Access denied")
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT COALESCE(SUM(a.points), 0) AS total_points
            FROM submissions sub
            JOIN activity_requests r ON sub.request_id = r.id
            JOIN activities a ON r.activity_id = a.id
            WHERE r.student_id = %s
              AND sub.status = 'approved';
            """,
            (student_id,)
        )

        total_points = cur.fetchone()[0]

        cur.close()
        conn.close()

        return {
            "student_id": student_id,
            "total_points": total_points
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/")
def get_all_students_with_points(admin=Depends(require_admin)):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT s.id, s.name, COALESCE(SUM(a.points), 0)
            FROM students s
            LEFT JOIN activity_requests r ON r.student_id = s.id
            LEFT JOIN submissions sub
                ON sub.request_id = r.id AND sub.status = 'approved'
            LEFT JOIN activities a ON r.activity_id = a.id
            GROUP BY s.id
            ORDER BY s.id;
            """
        )

        rows = cur.fetchall()
        cur.close()
        conn.close()

        return [
            {
                "student_id": r[0],
                "name": r[1],
                "total_points": r[2],
            }
            for r in rows
        ]

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
