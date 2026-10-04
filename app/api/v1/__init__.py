from fastapi import APIRouter

from app.api.v1 import auth, destinations, hotels, packages

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(destinations.router)
api_router.include_router(packages.router)
api_router.include_router(hotels.router)
