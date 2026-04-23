from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta

from . import models, schemas
from .database import SessionLocal

router = APIRouter()

# =========================
# DB Dependency
# =========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================
# Auth Setup
# =========================
SECRET_KEY = "secret"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# =========================
# Password Functions
# =========================
def hash_password(password: str):
    return pwd_context.hash(password[:72])  # fix bcrypt issue

def verify_password(plain, hashed):
    return pwd_context.verify(plain[:72], hashed)

# =========================
# Token Creation
# =========================
def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# =========================
# Get Current User
# =========================
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# =========================
# AUTH ROUTES
# =========================

@router.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = models.User(
        username=user.username,
        password=hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully"}

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_token({"sub": user.username})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

# =========================
# DOCTOR ROUTES
# =========================

@router.post("/doctors")
def create_doctor(doctor: schemas.DoctorCreate, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    new_doc = models.Doctor(**doctor.dict())
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    return new_doc

@router.get("/doctors")
def get_doctors(specialization: str = None, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    query = db.query(models.Doctor)
    if specialization:
        query = query.filter(models.Doctor.specialization == specialization)
    return query.all()

@router.put("/doctors/{doctor_id}")
def update_doctor(doctor_id: int, doctor: schemas.DoctorCreate, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    doc = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found")

    for key, value in doctor.dict().items():
        setattr(doc, key, value)

    db.commit()
    return doc

@router.delete("/doctors/{doctor_id}")
def delete_doctor(doctor_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    doc = db.query(models.Doctor).filter(models.Doctor.id == doctor_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found")

    db.delete(doc)
    db.commit()
    return {"message": "Doctor deleted"}

# =========================
# PATIENT ROUTES
# =========================

@router.post("/patients")
def create_patient(patient: schemas.PatientCreate, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    new_patient = models.Patient(**patient.dict())
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    return new_patient

@router.get("/patients")
def get_patients(search: str = None, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    query = db.query(models.Patient)
    if search:
        query = query.filter(models.Patient.name.contains(search))
    return query.all()

@router.put("/patients/{patient_id}")
def update_patient(patient_id: int, patient: schemas.PatientCreate, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    pat = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not pat:
        raise HTTPException(status_code=404, detail="Patient not found")

    for key, value in patient.dict().items():
        setattr(pat, key, value)

    db.commit()
    return pat

@router.delete("/patients/{patient_id}")
def delete_patient(patient_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    pat = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not pat:
        raise HTTPException(status_code=404, detail="Patient not found")

    db.delete(pat)
    db.commit()
    return {"message": "Patient deleted"}

# =========================
# APPOINTMENT ROUTES
# =========================

@router.post("/appointments")
def create_appointment(app: schemas.AppointmentCreate, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    new_app = models.Appointment(**app.dict())
    db.add(new_app)
    db.commit()
    db.refresh(new_app)
    return new_app

@router.get("/appointments")
def get_appointments(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    return db.query(models.Appointment).all()

@router.get("/appointments/doctor/{doctor_id}")
def get_by_doctor(doctor_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    return db.query(models.Appointment).filter(models.Appointment.doctor_id == doctor_id).all()

@router.get("/appointments/patient/{patient_id}")
def get_by_patient(patient_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    return db.query(models.Appointment).filter(models.Appointment.patient_id == patient_id).all()

@router.delete("/appointments/{appointment_id}")
def cancel_appointment(appointment_id: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    app = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Appointment not found")

    db.delete(app)
    db.commit()
    return {"message": "Appointment cancelled"}
