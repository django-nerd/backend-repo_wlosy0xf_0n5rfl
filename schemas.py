"""
Database Schemas for Dine-In Preorder App

Each Pydantic model maps to a MongoDB collection with the lowercased class name.
- Restaurant -> "restaurant"
- MenuItem -> "menuitem"
- Order -> "order"
"""

from pydantic import BaseModel, Field
from typing import Optional, List

class Restaurant(BaseModel):
    name: str = Field(..., description="Restaurant name")
    address: str = Field(..., description="Street address")
    cuisine: str = Field(..., description="Cuisine type, e.g., Indian, Italian")
    image: Optional[str] = Field(None, description="Hero image URL")
    avg_prep_minutes: int = Field(20, ge=1, le=180, description="Average prep time per order in minutes")

class MenuItem(BaseModel):
    restaurant_id: str = Field(..., description="Restaurant ID (stringified ObjectId)")
    name: str = Field(..., description="Menu item name")
    description: Optional[str] = Field(None, description="Short description")
    price: float = Field(..., ge=0, description="Price in local currency")
    category: Optional[str] = Field(None, description="Category such as Starter, Main, Dessert")
    image: Optional[str] = Field(None, description="Image URL")
    is_available: bool = Field(True, description="Availability flag")

class OrderItem(BaseModel):
    menu_item_id: str
    quantity: int = Field(1, ge=1)

class Order(BaseModel):
    restaurant_id: str
    customer_name: str
    customer_phone: str
    dine_in_time: str = Field(..., description="ISO datetime string for desired dine-in time")
    items: List[OrderItem]
    special_requests: Optional[str] = None
    total: Optional[float] = Field(None, ge=0)
