import pandas as pd
from pydantic import BaseModel, ValidationError, validator

# Define a Pydantic model for claim data
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

# Load CSV file
df = pd.read_csv('claims.csv')

# Validate each row
valid_claims = []
invalid_claims = []

for _, row in df.iterrows():
    try:
        claim = Claim(**row.to_dict())
        valid_claims.append(claim.dict())
    except ValidationError as e:
        invalid_claims.append({"data": row.to_dict(), "errors": e.errors()})

# Save results to separate files
pd.DataFrame(valid_claims).to_csv('valid_claims.csv', index=False)
pd.DataFrame(invalid_claims).to_csv('invalid_claims.csv', index=False)

print(f"Valid claims: {len(valid_claims)}")
print(f"Invalid claims: {len(invalid_claims)}")