from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.donation import Donation
from app.models.message import Message
from app.models.user import User
from app.services.notifications import create_notification

router = APIRouter(prefix="/api/donations", tags=["messages"])


class MessageIn(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


def _accepted_donation(db: Session, donation_id: str, user: User) -> Donation:
    """Only the donor, the accepted NGO and admins may use contact/chat, and only
    once an NGO has accepted the donation."""
    d = db.query(Donation).filter(Donation.id == donation_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Donation not found")
    if not d.accepted_ngo_id:
        raise HTTPException(status_code=400, detail="Contact and chat open once an NGO accepts the donation")
    if user.role != "admin" and user.id not in (d.donor_id, d.accepted_ngo_id):
        raise HTTPException(status_code=403, detail="You do not have access to this donation")
    return d


@router.get("/{donation_id}/contact")
def donation_contact(donation_id: str, db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    d = _accepted_donation(db, donation_id, current_user)
    donor = db.query(User).filter(User.id == d.donor_id).first()
    ngo = db.query(User).filter(User.id == d.accepted_ngo_id).first()

    def card(u):
        return {"name": u.name, "phone": u.phone, "email": u.email, "address": u.address}

    return {"donor": card(donor), "ngo": card(ngo)}


@router.get("/{donation_id}/messages")
def list_messages(donation_id: str, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    d = _accepted_donation(db, donation_id, current_user)
    msgs = (db.query(Message).filter(Message.donation_id == d.id)
            .order_by(Message.created_at.asc()).all())
    names = {u.id: u.name for u in db.query(User).filter(User.id.in_({m.sender_id for m in msgs})).all()} if msgs else {}
    return [{"id": m.id, "sender_id": m.sender_id, "sender_name": names.get(m.sender_id, "?"),
             "text": m.text, "created_at": m.created_at, "mine": m.sender_id == current_user.id} for m in msgs]


@router.post("/{donation_id}/messages", status_code=201)
def send_message(donation_id: str, payload: MessageIn, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    d = _accepted_donation(db, donation_id, current_user)
    if current_user.role == "admin":
        raise HTTPException(status_code=403, detail="Admins can read but not send messages")
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=422, detail="Message cannot be empty")
    m = Message(donation_id=d.id, sender_id=current_user.id, text=text)
    db.add(m)
    other = d.accepted_ngo_id if current_user.id == d.donor_id else d.donor_id
    create_notification(db, other, f"New message from {current_user.name} about '{d.food_type}': {text[:80]}",
                        "message", d.id, commit=False)
    db.commit()
    db.refresh(m)
    return {"id": m.id, "sender_id": m.sender_id, "sender_name": current_user.name,
            "text": m.text, "created_at": m.created_at, "mine": True}
