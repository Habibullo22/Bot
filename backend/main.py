import os
import sqlite3
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ADMIN_ID = 5815294733  # seniki

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "users.db")
WEBAPP_DIR = os.path.join(BASE_DIR, "webapp")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # hozircha oson
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def db_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        usdt REAL DEFAULT 0,
        rub  REAL DEFAULT 0,
        uzs  INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS deposits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        currency TEXT,
        amount REAL,
        status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

init_db()

# WebApp static fayllar
app.mount("/static", StaticFiles(directory=WEBAPP_DIR), name="static")

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(WEBAPP_DIR, "index.html"))

@app.get("/api/health")
def health():
    return {"ok": True}

@app.post("/api/user/upsert")
def upsert_user(user_id: int, username: str = ""):
    conn = db_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
        (user_id, username)
    )
    cur.execute(
        "UPDATE users SET username=? WHERE user_id=?",
        (username, user_id)
    )
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.get("/api/balance/{user_id}")
def balance(user_id: int):
    conn = db_conn()
    cur = conn.cursor()
    cur.execute("SELECT usdt, rub, uzs FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(404, "User not found")
    return {"usdt": row["usdt"], "rub": row["rub"], "uzs": row["uzs"]}

@app.post("/api/deposit/request")
def deposit_request(user_id: int, currency: str, amount: float):
    currency = currency.lower().strip()
    if currency not in ("usdt", "rub", "uzs"):
        raise HTTPException(400, "Bad currency")
    if amount <= 0:
        raise HTTPException(400, "Amount must be > 0")

    conn = db_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(404, "User not found")

    cur.execute(
        "INSERT INTO deposits (user_id, currency, amount) VALUES (?, ?, ?)",
        (user_id, currency, amount)
    )
    conn.commit()
    conn.close()
    return {"status": "pending"}

@app.post("/api/admin/add_balance")
def admin_add_balance(
    admin_id: int = Query(...),
    user_id: int = Query(...),
    usdt: float = 0,
    rub: float = 0,
    uzs: int = 0,
):
    if admin_id != ADMIN_ID:
        raise HTTPException(403, "Not admin")

    conn = db_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(404, "User not found")

    cur.execute("""
        UPDATE users
        SET usdt = usdt + ?,
            rub  = rub  + ?,
            uzs  = uzs  + ?
        WHERE user_id = ?
    """, (usdt, rub, uzs, user_id))
    conn.commit()
    conn.close()
    return {"status": "ok"}

