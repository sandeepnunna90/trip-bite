from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from backend.routers.auth import get_current_user
from backend.routers.trips import get_trip
from backend.services.pdf_service import render_trip_pdf

router = APIRouter()


@router.get("/pdf/{trip_id}")
def export_pdf(trip_id: str, user: dict = Depends(get_current_user)):
    trip = get_trip(trip_id, user)  # reuses auth check + data loading
    trip_dict = trip.model_dump()

    try:
        pdf_bytes = render_trip_pdf(trip_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="trip-{trip_id[:8]}.pdf"'},
    )
