"""
Central config. Reads .env and exposes which LLM provider/model to use.
Keeping this in one place means swapping Groq <-> NVIDIA NIM never touches
agent logic.
"""
import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")  # "groq" | "nvidia_nim"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
RAZORPAY_ENABLED = bool(RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)
RAZORPAY_MAX_LINKS_PER_BATCH = int(os.getenv("RAZORPAY_MAX_LINKS_PER_BATCH", "3"))

# --- Policy engine constants (the "bounded and gated" rules) ---
MAX_RETRIES_PER_TRANSACTION = 3
DISCOUNT_CAP_PERCENT = 5          # negotiation agent can never offer more than this
MAX_INSTALLMENTS = 3              # negotiation agent can never split into more than this
RECONCILIATION_MIN_MATCH_RATE = 0.85  # orchestrator halts downstream steps below this
LOW_VALUE_TRANSACTION_THRESHOLD = 200  # below this, auto-handle only, never escalate to human
