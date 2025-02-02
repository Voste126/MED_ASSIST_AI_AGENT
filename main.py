from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import pandas as pd
from pydantic import BaseModel, ValidationError, validator
import os
import africastalking  # Import Africa's Talking library
from dotenv import load_dotenv

app = FastAPI()

load_dotenv()

# Initialize Africa's Talking SDK
africastalking_username = os.environ.get("AFRICASTALKING_USERNAME")  # Your Africa's Talking username
africastalking_api_key = os.environ.get("AFRICASTALKING_API_KEY")    # Your Africa's Talking API key

# Initialize the SDK
africastalking.initialize(africastalking_username, africastalking_api_key)

# Get the SMS service
sms = africastalking.SMS

# Define the Claim model
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

# Endpoint to notify users about invalid claims via SMS (Africa's Talking)
@app.post("/notify/sms/")
async def notify_invalid_claims(invalid_claims: list[dict]):
    recipient_phone_number = "+254769475680"  # Replace with the recipient's phone number in E.164 format

    for claim in invalid_claims:
        message_body = f"Claim {claim['data']['claim_id']} has errors: {claim['errors']}"
        try:
            # Send the SMS
            response = sms.send(message_body, [recipient_phone_number])
            print(f"SMS sent successfully: {response}")
        except Exception as e:
            print(f"Failed to send SMS: {str(e)}")

    return {"message": f"Notified {len(invalid_claims)} users about invalid claims"}

# Optional: Endpoint to notify users about invalid claims via email (SendGrid)
# If you still want to keep the email functionality, uncomment this section.
"""
@app.post("/notify/email/")
async def notify_invalid_claims_email(invalid_claims: list[dict]):
    SENDGRID_API_KEY = "your_sendgrid_api_key"
    for claim in invalid_claims:
        message = Mail(
            from_email="from@example.com",
            to_emails="to@example.com",
            subject=f"Error in Claim {claim['data']['claim_id']}",
            plain_text_content=f"Claim {claim['data']['claim_id']} has errors: {claim['errors']}"
        )
        try:
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            response = sg.send(message)
        except Exception as e:
            print(str(e))
    return {"message": f"Notified {len(invalid_claims)} users about invalid claims via email"}
"""