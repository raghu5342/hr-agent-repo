from app.agents.ats_agent import ats_graph
from fastapi import FastAPI, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import engine, Base, get_db
from app.models.candidate import Candidate

Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "HR Agent Running Successfully"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/upload-resume")
async def upload_resume(
    name: str = Form(...),
    email: str = Form(...),
    role_applied: str = Form(...),
    resume: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    content = await resume.read()
    text = content.decode(errors="ignore").lower()

    result = ats_graph.invoke({
        "resume_text": text,
        "score": 0,
        "stage": ""
    })

    score = result["score"]
    stage = result["stage"]

    candidate = Candidate(
        name=name,
        email=email,
        role_applied=role_applied,
        ats_score=score,
        stage=stage
    )

    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    return {
        "message": "Resume Uploaded",
        "candidate_id": candidate.id,
        "ats_score": score,
        "stage": stage
    }


@app.get("/candidates")
async def get_candidates(db: Session = Depends(get_db)):
    data = db.query(Candidate).all()

    result = []

    for c in data:
        result.append({
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "role_applied": c.role_applied,
            "ats_score": c.ats_score,
            "tech_score": c.tech_score,
            "hr_score": c.hr_score,
            "stage": c.stage
        })

    return result


@app.put("/update-stage/{candidate_id}")
async def update_stage(
    candidate_id: int,
    stage: str,
    db: Session = Depends(get_db)
):
    candidate = db.query(Candidate).filter(
        Candidate.id == candidate_id
    ).first()

    if not candidate:
        return {"error": "Candidate not found"}

    candidate.stage = stage

    db.commit()
    db.refresh(candidate)

    return {
        "message": "Stage Updated Successfully",
        "candidate_id": candidate.id,
        "new_stage": candidate.stage
    }