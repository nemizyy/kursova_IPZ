from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import shutil

try:
    from .service import InventoryService
    from .observer import EventType
except ImportError:
    from backend.service import InventoryService
    from backend.observer import EventType

app = FastAPI(title="Inventory API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service = InventoryService()

# ─── Upload directory ──────────────────────────────────────
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "images")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ─── Pydantic schemas ──────────────────────────────────────

class ItemCreate(BaseModel):
    inventory_number: str = Field(..., max_length=50)
    name: str
    category: str
    cost: float = Field(..., ge=0)
    location: Optional[str] = ""
    description: Optional[str] = ""
    purchase_date: Optional[str] = ""

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    cost: Optional[float] = None
    location: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    purchase_date: Optional[str] = None

class FilterParams(BaseModel):
    min_cost: Optional[float] = None
    max_cost: Optional[float] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    status: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None

class CategoryCreate(BaseModel):
    name: str
    label: str
    parent_name: Optional[str] = None

class CategoryUpdate(BaseModel):
    label: Optional[str] = None
    parent_name: Optional[str] = None

# ─── API endpoints ───────────────────────────────────────

@app.post("/api/items", response_model=dict)
def add_item(payload: ItemCreate):
    try:
        item = service.add_item(
            inventory_number=payload.inventory_number,
            name=payload.name,
            category=payload.category,
            cost=payload.cost,
            location=payload.location or "",
            description=payload.description or "",
            purchase_date=payload.purchase_date or "",
        )
        return {"status": "added", "item": item.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/items", response_model=List[dict])
def list_items():
    return [i.to_dict() for i in service.get_all_items()]

# IMPORTANT: search must come BEFORE /{inv} to avoid route conflicts
@app.get("/api/items/search", response_model=List[dict])
def search_items(q: str = Query(...)):
    return [i.to_dict() for i in service.search_items(q)]

@app.get("/api/items/filter", response_model=List[dict])
def filter_items(
    min_cost: Optional[float] = None,
    max_cost: Optional[float] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    location: Optional[str] = None,
):
    """Фільтрація майна за будь-якою комбінацією параметрів (Req 3.2)."""
    return [i.to_dict() for i in service.filter_items(
        min_cost=min_cost,
        max_cost=max_cost,
        date_from=date_from,
        date_to=date_to,
        status=status,
        category=category,
        location=location,
    )]

@app.get("/api/items/{inv}", response_model=dict)
def get_item(inv: str):
    item = service.get_item(inv)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item.to_dict()

@app.patch("/api/items/{inv}")
def edit_item(inv: str, payload: ItemUpdate):
    fields = {k: v for k, v in payload.dict().items() if v is not None}
    try:
        service.edit_item(inv, **fields)
        return {"status": "updated", "inventory_number": inv}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/items/{inv}")
def delete_item(inv: str):
    try:
        service.delete_item(inv)
        return {"status": "deleted", "inventory_number": inv}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/items/{inv}/move")
def move_item(inv: str, to: str = Query(...)):
    try:
        service.move_item(inv, to)
        return {"status": "moved", "inventory_number": inv, "new_location": to}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/items/{inv}/write_off")
def write_off_item(inv: str, reason: str = ""):
    try:
        service.write_off_item(inv, reason)
        return {"status": "written_off", "inventory_number": inv}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ─── Photo upload (Req 1.3) ─────────────────────────────────

@app.post("/api/items/{inv}/photo")
async def upload_photo(inv: str, file: UploadFile = File(...)):
    """Завантажити фото для об'єкта майна."""
    item = service.get_item(inv)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Непідтримуваний тип файлу: {file.content_type}. Дозволені: JPEG, PNG, WebP, GIF."
        )

    # Generate unique filename
    ext = os.path.splitext(file.filename)[1] or ".jpg"
    filename = f"{inv}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    # Save file
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Update item's photo_path
    photo_url = f"/api/photos/{filename}"
    service.edit_item(inv, photo_path=photo_url)

    return {"status": "uploaded", "photo_path": photo_url}

@app.get("/api/photos/{filename}")
async def get_photo(filename: str):
    """Повернути фото майна."""
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="Photo not found")
    return FileResponse(filepath)

# ─── History ─────────────────────────────────────────────────

@app.get("/api/history", response_model=List[dict])
def all_history():
    return [r.to_dict() for r in service.get_history()]

@app.get("/api/history/{inv}", response_model=List[dict])
def item_history(inv: str):
    return [r.to_dict() for r in service.get_history(inv)]

# ─── Reports ─────────────────────────────────────────────────

@app.get("/api/report/{type}")
def generate_report(type: str, date_from: Optional[str] = None, date_to: Optional[str] = None):
    try:
        if type == "value_period" and date_from and date_to:
            report = service.generate_value_period_report(date_from, date_to)
        else:
            report = service.generate_report(report_type=type)
        return {"type": type, "report": report}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ─── Categories ──────────────────────────────────────────────

@app.get("/api/categories", response_model=List[dict])
def list_categories():
    return [c.to_dict() for c in service.get_categories()]

@app.get("/api/categories/hierarchy")
def get_hierarchy():
    return service.get_category_hierarchy()

@app.post("/api/categories")
def add_category(payload: CategoryCreate):
    try:
        cat = service.add_category(payload.name, payload.label, payload.parent_name)
        return {"status": "added", "category": cat.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.patch("/api/categories/{name}")
def edit_category(name: str, payload: CategoryUpdate):
    try:
        service.edit_category(name, payload.label, payload.parent_name)
        return {"status": "updated", "name": name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/categories/{name}")
def delete_category(name: str):
    try:
        service.delete_category(name)
        return {"status": "deleted", "name": name}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ─── Stats ───────────────────────────────────────────────────

@app.get("/api/stats")
def get_stats():
    items = service.get_all_items()
    categories = service.get_categories()
    total_cost = sum(i.cost for i in items)
    active = sum(1 for i in items if i.status == "active")
    written_off = sum(1 for i in items if i.status == "written_off")
    return {
        "total_items": len(items),
        "active_items": active,
        "written_off": written_off,
        "total_cost": total_cost,
        "categories": len(categories)
    }

# ─── Undo / Redo ────────────────────────────────────────────

@app.post("/api/undo")
def undo():
    return {"undo": service.undo()}

@app.post("/api/redo")
def redo():
    return {"redo": service.redo()}

# ─── Static Files & SPA Fallback ───────────────────────────

dist_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "dist")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # Check if frontend is built
    if not os.path.exists(dist_path):
        if full_path == "":
            return {"message": "Inventory API is running. Build frontend with 'npm run build' in /web to see the UI."}
        raise HTTPException(status_code=404, detail="Not Found")

    # Try to serve specific file (e.g. assets, favicon)
    file_path = os.path.join(dist_path, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # Fallback to index.html for SPA routing
    index_path = os.path.join(dist_path, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    raise HTTPException(status_code=404, detail="Frontend index.html not found")
