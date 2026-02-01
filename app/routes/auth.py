from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.db import get_connection
from app.auth.auth import create_access_token
from app.auth.dependencies import get_current_user, require_admin, require_student

router = APIRouter(prefix="/auth", tags=["Auth"])

class AdminLogin(BaseModel):
    email: str

@router.post("/admin/login")
def admin_login(data: AdminLogin):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id FROM admins WHERE email = %s;",
        (data.email,)
    )

    admin = cur.fetchone()
    cur.close()
    conn.close()

    if admin is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "user_id": admin[0],
        "role": "admin"
    })

    return {"access_token": token, "token_type": "bearer"}

class StudentLogin(BaseModel):
    usn: str
    name: str
    email: str

@router.post("/student/login")
def student_login(data: StudentLogin):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id FROM students WHERE usn = %s;",
        (data.usn,)
    )

    student = cur.fetchone()

    if student is None:
        cur.execute(
            """
            INSERT INTO students (name, usn, email)
            VALUES (%s, %s, %s)
            RETURNING id;
            """,
            (data.name, data.usn, data.email)
        )
        student_id = cur.fetchone()[0]
        conn.commit()
    else:
        student_id = student[0]

    cur.close()
    conn.close()

    token = create_access_token({
        "user_id": student_id,
        "role": "student"
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }
