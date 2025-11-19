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


# Seed endpoint to create demo restaurants + menus
@app.post("/seed")
def seed_demo():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    restaurants_data = [
        {
            "name": "Blue Flame Bistro",
            "address": "123 Flavor Street",
            "cuisine": "Fusion",
            "image": "https://images.unsplash.com/photo-1541542684-4a7a2e4b6c56?w=1200&q=80&auto=format&fit=crop",
            "avg_prep_minutes": 20,
            "menu": [
                {"name": "Smoky Paneer Tacos", "description": "Cilantro crema, pickled onions", "price": 8.5, "category": "Starters", "image": "https://images.unsplash.com/photo-1604908554007-43f9e8ae4b6b?w=900&auto=format&fit=crop&q=80"},
                {"name": "Fire-Grilled Chicken", "description": "Herb butter, charred lemon", "price": 14.0, "category": "Mains", "image": "https://images.unsplash.com/photo-1555992336-03a23cda0d05?w=900&auto=format&fit=crop&q=80"},
                {"name": "Truffle Mushroom Pasta", "description": "Parmesan, garlic crumbs", "price": 13.5, "category": "Mains", "image": "https://images.unsplash.com/photo-1525755662778-989d0524087e?w=900&auto=format&fit=crop&q=80"},
                {"name": "Molten Lava Cake", "description": "Vanilla gelato", "price": 6.0, "category": "Desserts", "image": "https://images.unsplash.com/photo-1541781286675-09c7838f7135?w=900&auto=format&fit=crop&q=80"},
                {"name": "Iced Hibiscus Tea", "description": "Fresh brewed", "price": 3.5, "category": "Drinks", "image": "https://images.unsplash.com/photo-1600275669439-14e40452d20e?w=900&auto=format&fit=crop&q=80"}
            ],
        },
        {
            "name": "Sunset Sushi",
            "address": "45 Ocean Ave",
            "cuisine": "Japanese",
            "image": "https://images.unsplash.com/photo-1553621042-f6e147245754?w=1200&q=80&auto=format&fit=crop",
            "avg_prep_minutes": 15,
            "menu": [
                {"name": "Salmon Nigiri", "description": "Fresh Atlantic salmon over rice", "price": 4.0, "category": "Sushi", "image": "https://images.unsplash.com/photo-1604908177073-028adf54b9f7?w=900&auto=format&fit=crop&q=80"},
                {"name": "Spicy Tuna Roll", "description": "Gochujang mayo, scallion", "price": 8.0, "category": "Rolls", "image": "https://images.unsplash.com/photo-1553621042-2a9b5d2a2403?w=900&auto=format&fit=crop&q=80"},
                {"name": "Tempura Udon", "description": "Crispy shrimp, dashi broth", "price": 12.0, "category": "Noodles", "image": "https://images.unsplash.com/photo-1604908554007-43f9e8ae4b6b?w=900&auto=format&fit=crop&q=80"},
                {"name": "Miso Soup", "description": "Tofu, wakame", "price": 3.0, "category": "Soups", "image": "https://images.unsplash.com/photo-1562967914-608f82629710?w=900&auto=format&fit=crop&q=80"}
            ],
        },
        {
            "name": "Pasta Piazza",
            "address": "88 Roma Street",
            "cuisine": "Italian",
            "image": "https://images.unsplash.com/photo-1520201163981-8cc95007dd2a?w=1200&q=80&auto=format&fit=crop",
            "avg_prep_minutes": 22,
            "menu": [
                {"name": "Margherita Pizza", "description": "San Marzano, buffalo mozzarella", "price": 11.0, "category": "Pizza", "image": "https://images.unsplash.com/photo-1548366086-7f1b3b4a6e6f?w=900&auto=format&fit=crop&q=80"},
                {"name": "Penne Arrabbiata", "description": "Chili, garlic, tomato", "price": 10.0, "category": "Pasta", "image": "https://images.unsplash.com/photo-1525755662778-989d0524087e?w=900&auto=format&fit=crop&q=80"},
                {"name": "Tiramisu", "description": "Espresso, mascarpone", "price": 6.5, "category": "Desserts", "image": "https://images.unsplash.com/photo-1601972599720-b0b01da2b362?w=900&auto=format&fit=crop&q=80"}
            ],
        },
        {
            "name": "Spice Route",
            "address": "12 Bazaar Lane",
            "cuisine": "Indian",
            "image": "https://images.unsplash.com/photo-1604908554007-43f9e8ae4b6b?w=1200&q=80&auto=format&fit=crop",
            "avg_prep_minutes": 25,
            "menu": [
                {"name": "Butter Chicken", "description": "Creamy tomato gravy", "price": 13.0, "category": "Mains", "image": "https://images.unsplash.com/photo-1604908817337-d28c52f4fb4b?w=900&auto=format&fit=crop&q=80"},
                {"name": "Paneer Tikka", "description": "Mint chutney", "price": 9.0, "category": "Starters", "image": "https://images.unsplash.com/photo-1617191519400-0b1d1f7a693c?w=900&auto=format&fit=crop&q=80"},
                {"name": "Garlic Naan", "description": "Wood-fired", "price": 3.0, "category": "Breads", "image": "https://images.unsplash.com/photo-1562967914-608f82629710?w=900&auto=format&fit=crop&q=80"}
            ],
        },
        {
            "name": "Green Bowl",
            "address": "5 Market Square",
            "cuisine": "Healthy",
            "image": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=1200&q=80&auto=format&fit=crop",
            "avg_prep_minutes": 12,
            "menu": [
                {"name": "Avo Quinoa Bowl", "description": "Lemon tahini", "price": 9.5, "category": "Bowls", "image": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=900&auto=format&fit=crop&q=80"},
                {"name": "Kale Caesar", "description": "Parmesan, sourdough crumbs", "price": 8.0, "category": "Salads", "image": "https://images.unsplash.com/photo-1551892374-ecf8754cf8d1?w=900&auto=format&fit=crop&q=80"},
                {"name": "Green Smoothie", "description": "Spinach, mango, coconut", "price": 5.0, "category": "Drinks", "image": "https://images.unsplash.com/photo-1514996937319-344454492b37?w=900&auto=format&fit=crop&q=80"}
            ],
        },
        {
            "name": "Burger Barn",
            "address": "77 Grove Rd",
            "cuisine": "American",
            "image": "https://images.unsplash.com/photo-1550547660-d9450f859349?w=1200&q=80&auto=format&fit=crop",
            "avg_prep_minutes": 18,
            "menu": [
                {"name": "Classic Cheeseburger", "description": "Aged cheddar, pickles", "price": 10.0, "category": "Burgers", "image": "https://images.unsplash.com/photo-1550547660-d9450f859349?w=900&auto=format&fit=crop&q=80"},
                {"name": "Sweet Potato Fries", "description": "Smoky aioli", "price": 4.0, "category": "Sides", "image": "https://images.unsplash.com/photo-1544025162-d76694265947?w=900&auto=format&fit=crop&q=80"},
                {"name": "Vanilla Shake", "description": "Madagascar vanilla", "price": 4.5, "category": "Drinks", "image": "https://images.unsplash.com/photo-1562967914-608f82629710?w=900&auto=format&fit=crop&q=80"}
            ],
        },
        {
            "name": "Taco Loco",
            "address": "101 Fiesta Blvd",
            "cuisine": "Mexican",
            "image": "https://images.unsplash.com/photo-1543352634-8730d3c4e20d?w=1200&q=80&auto=format&fit=crop",
            "avg_prep_minutes": 14,
            "menu": [
                {"name": "Carne Asada Taco", "description": "Pico de gallo", "price": 3.5, "category": "Tacos", "image": "https://images.unsplash.com/photo-1601050690114-c0e6c7a9b0e7?w=900&auto=format&fit=crop&q=80"},
                {"name": "Elote", "description": "Cotija, chili lime", "price": 4.0, "category": "Street", "image": "https://images.unsplash.com/photo-1605475010773-6021142438df?w=900&auto=format&fit=crop&q=80"},
                {"name": "Churros", "description": "Cinnamon sugar", "price": 5.0, "category": "Desserts", "image": "https://images.unsplash.com/photo-1541781286675-09c7838f7135?w=900&auto=format&fit=crop&q=80"}
            ],
        }
    ]

    created = []
    for r in restaurants_data:
        # Skip if a restaurant with same name exists
        existing = db["restaurant"].find_one({"name": r["name"]})
        if existing:
            continue
        rid = create_document("restaurant", Restaurant(**{k: r[k] for k in ["name", "address", "cuisine", "image", "avg_prep_minutes"]}))
        created.append(rid)
        for m in r.get("menu", []):
            mi = MenuItem(restaurant_id=rid, **m)
            create_document("menuitem", mi)

    if not created:
        return {"status": "ok", "message": "Seed already applied"}

    return {"status": "ok", "restaurants_created": len(created), "ids": created}


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
