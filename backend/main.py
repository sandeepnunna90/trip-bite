from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import restaurants, dishes, trips, share, export, auth

app = FastAPI(title="TripBite API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(restaurants.router, prefix="/restaurants", tags=["restaurants"])
app.include_router(dishes.router, prefix="/dishes", tags=["dishes"])
app.include_router(trips.router, prefix="/trips", tags=["trips"])
app.include_router(share.router, prefix="/share", tags=["share"])
app.include_router(export.router, prefix="/export", tags=["export"])


@app.get("/health")
def health():
    return {"status": "ok"}
