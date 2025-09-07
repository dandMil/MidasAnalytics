# routes/daily_summary_routes.py

from fastapi import APIRouter
from services.daily_summary.daily_summary_service import generate_daily_summary
#
router = APIRouter()

# @router.get("/midas/daily_summary")
# def get_daily_summary():
#     return generate_daily_summary()
