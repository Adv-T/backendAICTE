from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.db import get_connection
from app.auth.dependencies import require_admin, require_student, get_current_user;

router = APIRouter()

class ActivityCreate(BaseModel):
    name: str
    points: int

#Both, admin and Student can run.
@router.get("/")
def get_activities():
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT id, name, points
            FROM activities
            WHERE is_active = true
            ORDER BY name;
            """
        )

        rows = cur.fetchall()
        cur.close()
        conn.close()

        return [
            {"id": r[0], "name": r[1], "points": r[2]}
            for r in rows
        ]

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


#ADMIN ONLY
@router.post("/")
def create_activity(activity: ActivityCreate, admin=Depends(require_admin)):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO activities (name, points)
            VALUES (%s, %s)
            RETURNING id;
            """,
            (activity.name, activity.points)
        )

        activity_id = cur.fetchone()[0]
        conn.commit()

        cur.close()
        conn.close()

        return {
            "activity_id": activity_id,
            "message": "Activity created"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

#ADMIN ONLY
@router.put("/{activity_id}/deactivate")
def deactivate_activity(activity_id: int, admin=Depends(require_admin)):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            UPDATE activities
            SET is_active = false
            WHERE id = %s
            RETURNING id;
            """,
            (activity_id,)
        )

        result = cur.fetchone()
        conn.commit()

        cur.close()
        conn.close()

        if result is None:
            raise HTTPException(status_code=404, detail="Activity not found")

        return {"message": "Activity deactivated"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

#Segment 3.4: Admin Reactivates an activity
@router.put("/{activity_id}/activate")
def activate_activity(activity_id: int, admin=Depends(require_admin)):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            UPDATE activities
            SET is_active = true
            WHERE id = %s
            RETURNING id;
            """,
            (activity_id,)
        )

        result = cur.fetchone()
        conn.commit()

        cur.close()
        conn.close()

        if result is None:
            raise HTTPException(status_code=404, detail="Activity not found")

        return {"message": "Activity activated"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
