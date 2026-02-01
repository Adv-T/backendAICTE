from fastapi import FastAPI
from app.routes import students, activities, requests, submissions, auth

app = FastAPI(title="AICTE Mini App API")

app.include_router(auth.router, prefix='/auth', tags=['Auth'])
app.include_router(students.router, prefix="/students", tags=["Students"])
app.include_router(requests.router, prefix="/activity-requests", tags=["Activity Requests"])
app.include_router(submissions.router, prefix="/submissions", tags=["Submissions"])
app.include_router(activities.router, prefix="/activities", tags=["Activities"])
