from fastapi import APIRouter, HTTPException, Depends,Request
from pydantic import BaseModel
from app.db import get_connection
from app.auth.auth import create_access_token
from app.auth.dependencies import get_current_user, require_admin, require_student
from app.auth.google_oauth import oauth

router = APIRouter(tags=["Auth"])

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



@router.get("/google/login")
async def google_login(request: Request):
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback", name="google_callback")
async def google_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")

    if not user_info:
        raise HTTPException(400, "OAuth failed")
    
    google_sub = user_info["sub"]
    email = user_info["email"]
    name = user_info.get("name")


    if not email.endswith("@sahyadri.edu.in"):
        raise HTTPException(403, "Only college emails allowed")

    conn = get_connection()
    cur = conn.cursor()


    cur.execute(
        "SELECT id FROM students WHERE google_sub = %s;",
        (google_sub,)
    )
    student = cur.fetchone()

    if not student:
        cur.execute(
            """
            INSERT INTO students (name, email, google_sub)
            VALUES (%s, %s, %s)
            RETURNING id;
            """,
            (name, email, google_sub)
        )
        student_id = cur.fetchone()[0]
        conn.commit()
    else:
        student_id = student[0]


    cur.close()
    conn.close()

    jwt_token = create_access_token({
        "user_id": student_id,
        "role": "student"
    })

    return {
        "access_token": jwt_token,
        "token_type": "bearer"
    }


"""
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
            
            INSERT INTO students (name, usn, email)
            VALUES (%s, %s, %s)
            RETURNING id;
            ,
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
"""