from pydantic import BaseModel
from datetime import datetime

# -------- AUTH --------
class UserCreate(BaseModel):
    username: str
    password: str

# -------- DOCTOR --------
class DoctorCreate(BaseModel):
    name: str
    specialization: str

class DoctorUpdate(BaseModel):
    name: str

# -------- PATIENT --------
class PatientCreate(BaseModel):
    name: str
    phone: str

class PatientUpdate(BaseModel):
    name: str

# -------- APPOINTMENT --------
class AppointmentCreate(BaseModel):
    doctor_id: int
    patient_id: int
    appointment_date: datetime
