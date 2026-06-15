from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from openai import OpenAI
import uuid
import os

app = FastAPI(title="AI Classroom API")

# ==========================
# OPENAI CONFIG
# ==========================

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"))

# ==========================
# IN-MEMORY STORAGE
# ==========================

quizzes = {}
results = {}

# ==========================
# MODELS
# ==========================

class QuestionRequest(BaseModel):
    topic: str
    questionType: str
    count: int = 5
    difficulty: str = "medium"
    bloomLevel: str = "Understand"
    language: str = "English"

class QuizCreateRequest(BaseModel):
    quizName: str
    topic: str
    duration: int

class JoinQuizRequest(BaseModel):
    joinCode: str
    studentName: str

class SubmitQuizRequest(BaseModel):
    sessionId: str
    studentName: str
    score: int

# ==========================
# GENERATE QUESTIONS
# ==========================

@app.post("/generate-questions")
async def generate_questions(req: QuestionRequest):

    prompt = f"""
Generate {req.count} {req.questionType} questions.

Topic: {req.topic}

Difficulty: {req.difficulty}

Bloom Level: {req.bloomLevel}

Language: {req.language}

Question Types:
mcq
truefalse
fillblanks
shortanswer
essay

Return ONLY valid JSON.

Format:

{{
  "questions":[
    {{
      "question":"",
      "options":["","","",""],
      "answer":"",
      "explanation":""
    }}
  ]
}}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ]
    )

    return {
        "topic": req.topic,
        "generated": response.choices[0].message.content
    }

# ==========================
# GENERATE MCQ
# ==========================

@app.post("/generate-mcq")
async def generate_mcq(req: QuestionRequest):
    req.questionType = "mcq"
    return await generate_questions(req)

# ==========================
# TRUE FALSE
# ==========================

@app.post("/generate-truefalse")
async def generate_tf(req: QuestionRequest):
    req.questionType = "truefalse"
    return await generate_questions(req)

# ==========================
# FILL BLANKS
# ==========================

@app.post("/generate-fillblanks")
async def generate_fill(req: QuestionRequest):
    req.questionType = "fillblanks"
    return await generate_questions(req)

# ==========================
# SHORT ANSWER
# ==========================

@app.post("/generate-shortanswer")
async def generate_short(req: QuestionRequest):
    req.questionType = "shortanswer"
    return await generate_questions(req)

# ==========================
# ESSAY
# ==========================

@app.post("/generate-essay")
async def generate_essay(req: QuestionRequest):
    req.questionType = "essay"
    return await generate_questions(req)

# ==========================
# CREATE QUIZ
# ==========================

@app.post("/create-quiz")
async def create_quiz(req: QuizCreateRequest):

    session_id = str(uuid.uuid4())

    join_code = str(uuid.uuid4())[:6].upper()

    quizzes[join_code] = {
        "sessionId": session_id,
        "quizName": req.quizName,
        "topic": req.topic,
        "duration": req.duration,
        "students": []
    }

    return {
        "sessionId": session_id,
        "joinCode": join_code
    }

# ==========================
# JOIN QUIZ
# ==========================

@app.post("/join-quiz")
async def join_quiz(req: JoinQuizRequest):

    if req.joinCode not in quizzes:
        raise HTTPException(
            status_code=404,
            detail="Quiz not found"
        )

    quizzes[req.joinCode]["students"].append(
        req.studentName
    )

    return {
        "message":"Joined Successfully",
        "quiz": quizzes[req.joinCode]
    }

# ==========================
# SUBMIT QUIZ
# ==========================

@app.post("/submit-quiz")
async def submit_quiz(req: SubmitQuizRequest):

    if req.sessionId not in results:
        results[req.sessionId] = []

    results[req.sessionId].append(
        {
            "student": req.studentName,
            "score": req.score
        }
    )

    return {
        "message":"Submission Saved"
    }

# ==========================
# RESULTS
# ==========================

@app.get("/quiz-results/{session_id}")
async def quiz_results(session_id: str):

    return {
        "sessionId": session_id,
        "results": results.get(session_id, [])
    }

# ==========================
# ANALYTICS
# ==========================

@app.get("/analytics/{session_id}")
async def analytics(session_id: str):

    data = results.get(session_id, [])

    if len(data) == 0:
        return {
            "message":"No results"
        }

    scores = [x["score"] for x in data]

    avg = sum(scores) / len(scores)

    return {
        "totalStudents": len(scores),
        "averageScore": avg,
        "highestScore": max(scores),
        "lowestScore": min(scores)
    }

# ==========================
# VALIDATE QUESTIONS
# ==========================

@app.post("/validate-questions")
async def validate_questions(payload: dict):

    questions = payload.get(
        "questions",
        []
    )

    unique_questions = set()

    duplicates = False

    for q in questions:

        text = q.get(
            "question",
            ""
        )

        if text in unique_questions:
            duplicates = True

        unique_questions.add(text)

    return {
        "duplicatesFound": duplicates,
        "qualityScore": 95
    }

# ==========================
# HEALTH CHECK
# ==========================

@app.get("/")
async def root():

    return {
        "status":"running",
        "service":"AI Classroom API"
    }
