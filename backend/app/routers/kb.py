import json
import os
import shutil
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..config import settings
from ..database import SessionLocal, get_db
from ..deps import get_current_user, require_admin
from ..models import Document, KnowledgeBase, User
from ..schemas import DocumentOut, KBCreate, KBOut
from ..services import rag
from ..services.document_loader import load_and_split

router = APIRouter()

ALLOWED_EXT = {".pdf", ".docx", ".txt", ".md", ".csv"}


def _validate_file_signature(ext: str, head: bytes) -> None:
    """校验文件头与扩展名是否匹配，防止上传伪装文件。"""
    if ext == ".pdf" and not head.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="文件内容不是有效的 PDF")
    if ext == ".docx" and not head.startswith(b"PK"):
        raise HTTPException(status_code=400, detail="文件内容不是有效的 Word 文档")
    if ext in {".txt", ".md", ".csv"} and b"\x00" in head:
        raise HTTPException(status_code=400, detail="文本文件包含二进制内容，无法解析")


def process_document(doc_id: int) -> None:
    """后台任务：解析 → 分块 → 向量化 → 入库。"""
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            return
        try:
            chunks = load_and_split(doc.file_path)
            rag.add_documents_to_kb(doc.kb_id, chunks, doc.filename, doc.id)
            doc.status = "ready"
            doc.chunk_count = len(chunks)
        except Exception as e:  # noqa: BLE001
            doc.status = "failed"
            doc.error = str(e)
        db.commit()
    finally:
        db.close()


@router.get("", response_model=list[KBOut])
def list_kbs(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(KnowledgeBase).all()


@router.post("", response_model=KBOut, status_code=201)
def create_kb(body: KBCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    kb = KnowledgeBase(name=body.name.strip(), description=body.description)
    db.add(kb)
    db.commit()
    db.refresh(kb)
    return kb


@router.delete("/{kb_id}")
def delete_kb(kb_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    rag.delete_vectorstore(kb_id)
    db.delete(kb)
    db.commit()
    return {"detail": "ok"}


@router.get("/{kb_id}/documents", response_model=list[DocumentOut])
def list_documents(
    kb_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    return db.query(Document).filter(Document.kb_id == kb_id).all()


@router.post("/{kb_id}/documents", response_model=DocumentOut, status_code=201)
async def upload_document(
    kb_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式：{ext}")

    # 内容校验：读取文件头确认与扩展名匹配，防止伪装文件
    file.file.seek(0)
    head = file.file.read(1024)
    file.file.seek(0)
    _validate_file_signature(ext, head)

    os.makedirs(settings.upload_dir, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}{ext}"
    dest = os.path.join(settings.upload_dir, stored_name)
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    doc = Document(kb_id=kb_id, filename=file.filename, file_path=dest, status="parsing")
    db.add(doc)
    db.commit()
    db.refresh(doc)

    background_tasks.add_task(process_document, doc.id)
    return doc


@router.delete("/{kb_id}/documents/{document_id}")
def delete_document(
    kb_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    doc = (
        db.query(Document)
        .filter(Document.id == document_id, Document.kb_id == kb_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    rag.delete_document_chunks(kb_id, document_id)
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except OSError:
            pass
    db.delete(doc)
    db.commit()
    return {"detail": "ok"}
