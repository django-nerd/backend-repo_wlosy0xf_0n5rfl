import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from database import db, create_document, get_documents
from schemas import Restaurant, MenuItem, Order, OrderItem
from bson.objectid import ObjectId

app = FastAPI(title="Dine-In Preorder API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utilities

def serialize_doc(doc: dict):
    doc = dict(doc)
    if doc.get("_id") is not None:
        doc["id"] = str(doc.pop("_id"))
    return doc


@app.get("/")
def root():
    return {"message": "Dine-In Preorder API running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# Seed endpoint to create demo restaurant + menu if empty
@app.post("/seed")
def seed_demo():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    restaurants = list(db["restaurant"].find({}).limit(1))
    if restaurants:
        return {"status": "ok", "message": "Data already seeded"}

    r = Restaurant(
        name="Blue Flame Bistro",
        address="123 Flavor Street",
        cuisine="Fusion",
        image="https://images.unsplash.com/photo-1541542684-4a7a2e4b6c56?w=1200&q=80&auto=format&fit=crop",
        avg_prep_minutes=20,
    )
    rid = create_document("restaurant", r)

    demo_menu = [
        MenuItem(restaurant_id=rid, name="Smoky Paneer Tacos", description="Cilantro crema, pickled onions", price=8.5, category="Starters"),
        MenuItem(restaurant_id=rid, name="Fire-Grilled Chicken", description="Herb butter, charred lemon", price=14.0, category="Mains"),
        MenuItem(restaurant_id=rid, name="Truffle Mushroom Pasta", description="Parmesan, garlic crumbs", price=13.5, category="Mains"),
        MenuItem(restaurant_id=rid, name="Molten Lava Cake", description="Vanilla gelato", price=6.0, category="Desserts"),
        MenuItem(restaurant_id=rid, name="Iced Hibiscus Tea", description="Fresh brewed", price=3.5, category="Drinks"),
    ]
    for item in demo_menu:
        create_document("menuitem", item)

    return {"status": "ok", "restaurant_id": rid}


# Restaurants
@app.get("/restaurants")
def list_restaurants():
    docs = get_documents("restaurant")
    return [serialize_doc(d) for d in docs]


@app.post("/restaurants")
def create_restaurant(body: Restaurant):
    rid = create_document("restaurant", body)
    return {"id": rid}


# Menu
@app.get("/restaurants/{restaurant_id}/menu")
def list_menu(restaurant_id: str):
    docs = get_documents("menuitem", {"restaurant_id": restaurant_id})
    return [serialize_doc(d) for d in docs]


@app.post("/restaurants/{restaurant_id}/menu")
def create_menu_item(restaurant_id: str, body: MenuItem):
    if body.restaurant_id != restaurant_id:
        # Ensure consistent restaurant id
        body = MenuItem(**{**body.model_dump(), "restaurant_id": restaurant_id})
    mid = create_document("menuitem", body)
    return {"id": mid}


# Orders
class PlaceOrderRequest(BaseModel):
    restaurant_id: str
    customer_name: str
    customer_phone: str
    dine_in_time: str
    items: List[OrderItem]
    special_requests: Optional[str] = None


@app.post("/orders")
def place_order(req: PlaceOrderRequest):
    # Compute total based on menu prices
    menu_ids = [ObjectId(i.menu_item_id) for i in req.items]
    menu_docs = list(db["menuitem"].find({"_id": {"$in": menu_ids}}))
    price_map = {str(d["_id"]): float(d.get("price", 0)) for d in menu_docs}

    total = 0.0
    for it in req.items:
        total += price_map.get(it.menu_item_id, 0) * it.quantity

    order = Order(
        restaurant_id=req.restaurant_id,
        customer_name=req.customer_name,
        customer_phone=req.customer_phone,
        dine_in_time=req.dine_in_time,
        items=[OrderItem(menu_item_id=i.menu_item_id, quantity=i.quantity) for i in req.items],
        special_requests=req.special_requests,
        total=round(total, 2),
    )

    oid = create_document("order", order)

    # ETA calculation: use restaurant avg_prep_minutes
    rest = db["restaurant"].find_one({"_id": ObjectId(req.restaurant_id)})
    avg_prep = rest.get("avg_prep_minutes", 20) if rest else 20

    return {"id": oid, "total": order.total, "estimated_prep_minutes": avg_prep}


@app.get("/orders")
def list_orders(restaurant_id: Optional[str] = None, limit: int = 50):
    filt = {"restaurant_id": restaurant_id} if restaurant_id else {}
    docs = get_documents("order", filt, limit)
    for d in docs:
        d = serialize_doc(d)
    return [serialize_doc(d) for d in docs]


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
