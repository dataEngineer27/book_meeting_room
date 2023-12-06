from fastapi import APIRouter, Request, status, Depends
from sqlalchemy.orm import Session
from starlette.templating import Jinja2Templates
from routers.settings import oauth, FRONTEND_URL
from starlette.responses import RedirectResponse, JSONResponse, HTMLResponse
from authlib.integrations.starlette_client import OAuthError
from crud import crud
from schemas.schemas import CreateUser, Token, GoogleToken
from utils.utils import CREDENTIALS_EXCEPTION, valid_email_from_db, get_db, create_token, get_current_user_email, google_auth
import requests


auth_router = APIRouter(
    prefix='/auth',
    tags=['auth']
)
templates = Jinja2Templates(directory="templates")


# @auth_router.get('/signup')
# async def login(request: Request):
#     redirect_uri = FRONTEND_URL  # This creates the url for our /auth endpoint
#     return await oauth.google.authorize_redirect(request, redirect_uri)


# @auth_router.get('/token')
# async def auth(request: Request, db: Session = Depends(get_db)):
#     try:
#         access_token = await oauth.google.authorize_access_token(request)
#     except OAuthError:
#         raise CREDENTIALS_EXCEPTION
#     # user_data = await oauth.google.parse_id_token(request, access_token)
#     if valid_email_from_db(email=access_token['userinfo']['email'], db=db):
#         # TODO: validate email in our database and generate JWT token
#         jwt_token = create_token(access_token['userinfo']['email'])
#         # TODO: return the JWT token to the user so it can make requests to our /api endpoint
#         return JSONResponse({'result': True, 'jwt_token': jwt_token})
#     else:
#         crud.create_user(db=db, form_data=access_token['userinfo'])
#         jwt_token = create_token(access_token['userinfo']['email'])
#         return JSONResponse({'result': True, 'access_token': jwt_token})


@auth_router.post("/login", status_code=status.HTTP_200_OK, response_model=Token)
async def auth(google_token: GoogleToken, db: Session = Depends(get_db)):
    user_info = requests.get(f"https://www.googleapis.com/oauth2/v1/userinfo?alt=json&access_token={google_token.token}")
    user_dict = user_info.json()
    user_obj = crud.add_user(db=db, form_data=user_dict)
    if user_obj:
        jwt_token = create_token(user_dict['id'])
        return JSONResponse({'user_id': user_dict['id'], 'jwt_token': jwt_token})


@auth_router.get('/logout', status_code=status.HTTP_200_OK)
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url='/')


@auth_router.get('/unprotected')
def test():
    return {'message': 'unprotected api_app endpoint'}


@auth_router.get('/protected')
def test2(current_email: str = Depends(get_current_user_email)):
    return {'message': 'protected api_app endpoint'}