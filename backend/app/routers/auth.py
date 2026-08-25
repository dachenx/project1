from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..core.limiter import limiter
from ..core.security import create_access_token, hash_password, verify_password
from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import ChangePasswordIn, TokenOut, UserCreate, UserOut

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=201)
@limiter.limit("20/minute")
def register(body: UserCreate, request: Request, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")
    if not body.username.strip() or not body.password:
        raise HTTPException(status_code=400, detail="用户名和密码不能为空")
    user = User(username=body.username.strip(), password_hash=hash_password(body.password), role="user")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenOut)
@limiter.limit("20/minute")
def login(body: UserCreate, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_access_token(user.username, user.role)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/change-password")
def change_password(
    body: ChangePasswordIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(body.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    if len(body.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少 6 位")
    user.password_hash = hash_password(body.new_password)
    db.commit()
    return {"detail": "密码修改成功"}
