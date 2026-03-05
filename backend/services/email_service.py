import resend
from backend.config import get_settings


def send_welcome_email(to: str, name: str) -> None:
    settings = get_settings()

    if settings.use_mock_resend:
        print(f"[MOCK EMAIL] Welcome email to {to} ({name})")
        return

    resend.api_key = settings.resend_api_key

    resend.Emails.send({
        "from": settings.resend_from_email,
        "to": to,
        "subject": "Welcome to TripBite! 🍽️",
        "html": f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
          <h1 style="color: #e63946;">Welcome to TripBite, {name}!</h1>
          <p>We're excited to have you. TripBite helps solo travelers discover the best dishes at top-rated restaurants — powered by AI.</p>
          <h3>Here's how to get started:</h3>
          <ol>
            <li><strong>Search</strong> for a city and cuisine</li>
            <li><strong>Explore</strong> top-rated restaurants (4.5★+ · 1,000+ reviews)</li>
            <li><strong>Discover</strong> AI-extracted top dishes from real reviews</li>
            <li><strong>Save</strong> restaurants to your trip list</li>
            <li><strong>Share</strong> or export your trip as a PDF</li>
          </ol>
          <p style="color: #888; font-size: 12px;">Happy travels! — The TripBite Team</p>
        </div>
        """,
    })
