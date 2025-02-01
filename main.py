from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import pandas as pd
from pydantic import BaseModel, ValidationError, validator
import os
from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

app = FastAPI()
# Twilio credentials
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")

# SendGrid API key
SENDGRID_API_KEY = "your_sendgrid_api_key"

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Define the Claim model (same as before)
class Claim(BaseModel):
    claim_id: int
    patient_name: str
    patient_id: int
    procedure_code: str
    service_date: str
    billing_amount: float
    insurance_provider: str

    @validator('procedure_code')
    def validate_procedure_code(cls, value):
        if len(value) != 5 or not value.isdigit():
            raise ValueError("Procedure code must be a 5-digit number")
        return value

    @validator('service_date')
    def validate_service_date(cls, value):
        try:
            pd.to_datetime(value)
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")
        return value

# Endpoint to upload claims file
@app.post("/upload/")
async def upload_claims(file: UploadFile = File(...)):
    # Save uploaded file
    with open(file.filename, "wb") as buffer:
        buffer.write(await file.read())

    # Load and validate claims
    df = pd.read_csv(file.filename)
    valid_claims = []
    invalid_claims = []

    for _, row in df.iterrows():
        try:
            claim = Claim(**row.to_dict())
            valid_claims.append(claim.dict())
        except ValidationError as e:
            invalid_claims.append({"data": row.to_dict(), "errors": e.errors()})

    # Clean up uploaded file
    os.remove(file.filename)

    # Return results
    return {
        "valid_claims": valid_claims,
        "invalid_claims": invalid_claims,
    }

# Endpoint to submit valid claims
@app.post("/submit/")
async def submit_claims(claims: list[dict]):
    # Simulate claims submission
    submitted_claims = []
    for claim in claims:
        # Add logic to submit claims to insurance providers
        submitted_claims.append({**claim, "status": "submitted"})
    return {"submitted_claims": submitted_claims}

# Endpoint to notify users about invalid claims
@app.post("/notify/")
async def notify_invalid_claims(invalid_claims: list[dict]):
    for claim in invalid_claims:
        message = client.messages.create(
            body=f"Claim {claim['claim_id']} has errors: {claim['errors']}",
            from_=TWILIO_PHONE_NUMBER,
            to="recipient_phone_number"
        )
    return {"message": f"Notified {len(invalid_claims)} users about invalid claims"}

# Endpoint to notify users about invalid claims via email
@app.post("/notify/email/")
async def notify_invalid_claims(invalid_claims: list[dict]):
    for claim in invalid_claims:
        message = Mail(
            from_email="from@example.com",
            to_emails="to@example.com",
            subject=f"Error in Claim {claim['claim_id']}",
            plain_text_content=f"Claim {claim['claim_id']} has errors: {claim['errors']}"
        )
        try:
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            response = sg.send(message)
        except Exception as e:
            print(str(e))
    return {"message": f"Notified {len(invalid_claims)} users about invalid claims"}
