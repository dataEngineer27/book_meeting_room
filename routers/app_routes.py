from fastapi import APIRouter, Depends, Response, status, HTTPException
from sqlalchemy.orm import Session

from schemas.schemas import *
from crud import crud
from utils.utils import get_db, get_current_user, email_sender
from datetime import datetime, date

app_router = APIRouter(
    prefix='/app',
    tags=['app']
)


# ----------------------- Actions with ROOMS ------------------------
@app_router.get("/rooms", response_model=List[GetRoom], status_code=200)
async def get_rooms(db: Session = Depends(get_db), current_user: GetUser = Depends(get_current_user)):
    return crud.get_all_rooms(db=db)


@app_router.get("/rooms/{id}", response_model=GetRoom, status_code=200)
async def get_room(id: int, response: Response, db: Session = Depends(get_db),
                   current_user: GetUser = Depends(get_current_user)):
    room = crud.get_room(id=id, db=db)
    if not room:
        response.status_code = status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room with the id not found!")
    return room


# --------------------- Actions with MEETINGS --------------------------
@app_router.get("/meetings", response_model=List[GetMeeting], status_code=200)
def get_meetings_of_room(room_id: int, query_date: date, db: Session = Depends(get_db),
                         current_user: GetUser = Depends(get_current_user)):
    specific_meetings = crud.get_all_meetings_of_room_by_date(room_id=room_id, date=query_date, db=db)
    if not specific_meetings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Planed meetings not found!")
    return specific_meetings


@app_router.get("/my-meetings", response_model=List[GetInvitation])
async def get_own_meetings(db: Session = Depends(get_db), current_user: GetUser = Depends(get_current_user)):  # user_id: int,
    return crud.get_all_user_meetings(user_id=current_user.id, db=db)


@app_router.post("/meetings", response_model=CreateMeeting, status_code=201)
async def create_meeting(form_data: CreateMeeting, db: Session = Depends(get_db),
                         current_user: GetUser = Depends(get_current_user)):
    created_meeting = crud.create_meeting(db=db, form_data=form_data)
    if not created_meeting:
        raise HTTPException(status_code=status.HTTP_302_FOUND, detail="The meeting with id already exists!")
    email_receivers = [current_user.email]
    for id in form_data.invited_users:
        created_invitation = crud.create_invitations(db=db, user_id=id, meeting_id=form_data.id)
        if not created_invitation:
            raise HTTPException(status_code=status.HTTP_302_FOUND, detail="The invitation with id already exists!")
        user_email = crud.get_user(id=id, db=db).email
        email_receivers.append(user_email)
    room = crud.get_room(id=form_data.room_id, db=db).name
    meeting_name = crud.get_meeting(id=form_data.id, db=db).name
    start_time = crud.get_meeting(id=form_data.id, db=db).start_time
    end_time = crud.get_meeting(id=form_data.id, db=db).end_time
    await email_sender(receivers=email_receivers, organizer=current_user.fullname, room=room,
                       meeting_name=meeting_name, start_time=start_time, end_time=end_time)
    return created_meeting


@app_router.delete("/meetings/{id}", status_code=204)
async def delete_meeting(id, db: Session = Depends(get_db), current_user: GetUser = Depends(get_current_user)):
    deleted_meeting = crud.delete_meeting(id=id, db=db)
    if not deleted_meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found!")
    return deleted_meeting


@app_router.put("/meetings/{id}", status_code=202)
async def update_meeting(id, meeting: CreateMeeting, db: Session = Depends(get_db), current_user: GetUser = Depends(get_current_user)):
    updated_meeting = crud.update_meeting(id=id, meeting=meeting, db=db)
    if not updated_meeting:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found!!")

    return updated_meeting


# ----------------- Actions with INVITATIONS -----------------------
# @app_router.post("/invitations", response_model=CreateInvitation, status_code=201)
# async def create_invitation(form_data: CreateInvitation, db: Session = Depends(get_db),
#                             current_user: GetUser = Depends(get_current_user)):
#     email_receivers = [current_user.email]
#     for id in form_data.user_id:
#         created_invitation = crud.create_invitations(db=db, user_id=id, meeting_id=form_data.meeting_id)
#         if not created_invitation:
#             raise HTTPException(status_code=status.HTTP_302_FOUND, detail="The invitation with id already exists!")
#         user_email = crud.get_user(id=id, db=db).email
#         email_receivers.append(user_email)
#     room = crud.get_room(id=form_data.room_id, db=db).name
#     meeting_name = crud.get_meeting(id=form_data.meeting_id, db=db).name
#     start_time = crud.get_meeting(id=form_data.meeting_id, db=db).start_time
#     end_time = crud.get_meeting(id=form_data.meeting_id, db=db).end_time
#     await email_sender(receivers=email_receivers, organizer=current_user.fullname, room=room,
#                        meeting_name=meeting_name, start_time=start_time, end_time=end_time)


@app_router.get("/invitations", response_model=List[GetInvitation])
async def get_invitations(db: Session = Depends(get_db), current_user: GetUser = Depends(get_current_user)):  # user_id: int
    return crud.get_all_user_invitations(user_id=current_user.id, db=db)
