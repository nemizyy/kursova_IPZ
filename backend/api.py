from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os

from .service import InventoryService
from .models import Item

app = FastAPI(title="Inventory API")

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service = InventoryService()

@app.get("/api/items")
def get_items():
    return service.get_all_items()

@app.post("/api/items")
async def add_item(
    inventory_number: str = Form(...),
    name: str = Form(...),
    category: str = Form(...),
    cost: float = Form(...),
    location: str = Form(""),
    description: str = Form(""),
    photo: Optional[UploadFile] = File(None)
):
    photo_path = ""
    if photo and photo.filename:
        os.makedirs("assets", exist_ok=True)
        photo_path = f"assets/{photo.filename}"
        with open(photo_path, "wb") as f:
            f.write(await photo.read())
            
    try:
        service.add_item(
            inventory_number=inventory_number,
            name=name,
            category=category,
            cost=cost,
            location=location,
            description=description,
            photo_path=photo_path
        )
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/items/{inventory_number}")
def delete_item(inventory_number: str):
    try:
        service.delete_item(inventory_number)
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/stats")
def get_stats():
    items = service.get_all_items()
    active_items = sum(1 for item in items if item.status == "active")
    written_off = sum(1 for item in items if item.status == "written_off")
    total_cost = sum(item.cost for item in items)
    categories = len(set(item.category for item in items))
    
    return {
        "total_items": len(items),
        "total_cost": total_cost,
        "categories": categories,
        "active_items": active_items,
        "written_off": written_off
    }

@app.get("/api/categories")
def get_categories():
    return service.available_categories()
