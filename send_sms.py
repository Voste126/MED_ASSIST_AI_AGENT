from twilio.rest import Client
import os
# Twilio credentials
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")  # Your Twilio phone number
RECIPIENT_PHONE_NUMBER = os.environ.get("RECIPIENT_PHONE_NUMBER") # Recipient's phone number

# Initialize Twilio client
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

try:
    # Send the message
    message = client.messages.create(
        body="This is a test message from Twilio.",
        from_=TWILIO_PHONE_NUMBER,
        to=RECIPIENT_PHONE_NUMBER
    )
    print(f"Message sent successfully! SID: {message.sid}")
except Exception as e:
    print(f"Failed to send message: {str(e)}")