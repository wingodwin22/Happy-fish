from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from decimal import Decimal

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="Boutique Surgelés API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: str  # "poisson" ou "viande"
    price: float
    stock: float  # Changed to float to support fractional quantities
    unit: str = "kg"  # unité de mesure
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProductCreate(BaseModel):
    name: str
    category: str
    price: float
    stock: float  # Changed to float to support fractional quantities
    unit: str = "kg"

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[float] = None  # Changed to float to support fractional quantities
    unit: Optional[str] = None

class Client(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    credit_limit: float = 0.0
    current_debt: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ClientCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    credit_limit: float = 0.0

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    credit_limit: Optional[float] = None

class SaleItem(BaseModel):
    product_id: str
    product_name: str
    quantity: float
    unit_price: float
    total_price: float

class Sale(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: Optional[str] = None
    client_name: str = "Client Anonyme"
    items: List[SaleItem]
    subtotal: float
    discount: float = 0.0
    total: float
    payment_method: str = "espèces"  # espèces, carte, crédit
    status: str = "terminée"  # terminée, en_attente, annulée
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    invoice_number: str = Field(default_factory=lambda: f"INV-{datetime.now().strftime('%Y%m%d-%H%M%S')}")

class SaleCreate(BaseModel):
    client_id: Optional[str] = None
    client_name: str = "Client Anonyme"
    items: List[dict]  # [{"product_id": "", "quantity": 1}]
    discount: float = 0.0
    payment_method: str = "espèces"

# Helper functions
def prepare_for_mongo(data):
    """Prepare data for MongoDB storage"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
    return data

def parse_from_mongo(item):
    """Parse data from MongoDB"""
    if isinstance(item, dict):
        for key, value in item.items():
            if isinstance(value, str) and 'T' in value and (value.endswith('Z') or '+' in value[-6:]):
                try:
                    item[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except:
                    pass
    return item

# Routes
@api_router.get("/")
async def root():
    return {"message": "API Boutique Surgelés - Opérationnelle"}

# Products endpoints
@api_router.post("/products", response_model=Product)
async def create_product(product: ProductCreate):
    product_dict = product.dict()
    product_obj = Product(**product_dict)
    product_data = prepare_for_mongo(product_obj.dict())
    await db.products.insert_one(product_data)
    return product_obj

@api_router.get("/products", response_model=List[Product])
async def get_products():
    products = await db.products.find().to_list(1000)
    return [Product(**parse_from_mongo(product)) for product in products]

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    product = await db.products.find_one({"id": product_id})
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return Product(**parse_from_mongo(product))

@api_router.put("/products/{product_id}", response_model=Product)
async def update_product(product_id: str, product_update: ProductUpdate):
    existing_product = await db.products.find_one({"id": product_id})
    if not existing_product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    update_data = {k: v for k, v in product_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    await db.products.update_one({"id": product_id}, {"$set": prepare_for_mongo(update_data)})
    
    updated_product = await db.products.find_one({"id": product_id})
    return Product(**parse_from_mongo(updated_product))

@api_router.get("/products/search/{query}")
async def search_products(query: str):
    """Rechercher des produits par nom pour auto-suggestion"""
    if len(query.strip()) < 2:
        return []
    
    # Recherche insensible à la casse avec regex
    regex_pattern = {"$regex": query.strip(), "$options": "i"}
    products = await db.products.find({"name": regex_pattern}).limit(10).to_list(10)
    return [{"id": p["id"], "name": p["name"], "price": p["price"], "stock": p["stock"], "unit": p["unit"]} for p in products]

@api_router.delete("/products/{product_id}")
async def delete_product(product_id: str):
    result = await db.products.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    return {"message": "Produit supprimé avec succès"}

# Clients endpoints
@api_router.post("/clients", response_model=Client)
async def create_client(client: ClientCreate):
    client_dict = client.dict()
    client_obj = Client(**client_dict)
    client_data = prepare_for_mongo(client_obj.dict())
    await db.clients.insert_one(client_data)
    return client_obj

@api_router.get("/clients", response_model=List[Client])
async def get_clients():
    clients = await db.clients.find().to_list(1000)
    return [Client(**parse_from_mongo(client)) for client in clients]

@api_router.get("/clients/{client_id}", response_model=Client)
async def get_client(client_id: str):
    client = await db.clients.find_one({"id": client_id})
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return Client(**parse_from_mongo(client))

@api_router.put("/clients/{client_id}", response_model=Client)
async def update_client(client_id: str, client_update: ClientUpdate):
    existing_client = await db.clients.find_one({"id": client_id})
    if not existing_client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    update_data = {k: v for k, v in client_update.dict().items() if v is not None}
    
    await db.clients.update_one({"id": client_id}, {"$set": prepare_for_mongo(update_data)})
    
    updated_client = await db.clients.find_one({"id": client_id})
    return Client(**parse_from_mongo(updated_client))

@api_router.delete("/clients/{client_id}")
async def delete_client(client_id: str):
    result = await db.clients.delete_one({"id": client_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return {"message": "Client supprimé avec succès"}

# Sales endpoints
@api_router.post("/sales", response_model=Sale)
async def create_sale(sale_data: SaleCreate):
    # Handle automatic client creation if client_name provided but no client_id
    client_id = sale_data.client_id
    client_name = sale_data.client_name
    is_new_client = False
    
    if not client_id and client_name and client_name.strip() != "Client Anonyme" and client_name.strip() != "":
        # Check if client already exists by name
        existing_client = await db.clients.find_one({"name": client_name.strip()})
        
        if existing_client:
            # Use existing client
            client_id = existing_client["id"]
            client_name = existing_client["name"]
        else:
            # Check if trying to sell on credit to new client (not allowed)
            if sale_data.payment_method == "crédit":
                raise HTTPException(
                    status_code=400, 
                    detail="Impossible de vendre à crédit à un nouveau client. Veuillez d'abord enregistrer le client avec une limite de crédit."
                )
            
            # Create new client automatically (only if not credit sale)
            new_client = Client(
                name=client_name.strip(),
                phone="",
                address="",
                email="",
                credit_limit=0.0,
                current_debt=0.0
            )
            client_data = prepare_for_mongo(new_client.dict())
            await db.clients.insert_one(client_data)
            client_id = new_client.id
            client_name = new_client.name
            is_new_client = True
    
    # Validate quantities before processing
    for item_data in sale_data.items:
        if item_data["quantity"] <= 0:
            raise HTTPException(status_code=400, detail="La quantité doit être supérieure à 0")
    
    # Calculate sale totals
    items = []
    subtotal = 0.0
    
    for item_data in sale_data.items:
        # Get product details
        product = await db.products.find_one({"id": item_data["product_id"]})
        if not product:
            raise HTTPException(status_code=404, detail=f"Produit {item_data['product_id']} non trouvé")
        
        # Check stock
        if product["stock"] < item_data["quantity"]:
            raise HTTPException(status_code=400, detail=f"Stock insuffisant pour {product['name']}")
        
        # Create sale item
        item_total = product["price"] * item_data["quantity"]
        sale_item = SaleItem(
            product_id=item_data["product_id"],
            product_name=product["name"],
            quantity=item_data["quantity"],
            unit_price=product["price"],
            total_price=item_total
        )
        items.append(sale_item)
        subtotal += item_total
        
        # Update product stock
        new_stock = product["stock"] - item_data["quantity"]
        await db.products.update_one(
            {"id": item_data["product_id"]}, 
            {"$set": {"stock": new_stock, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    # Calculate final total
    total = subtotal - sale_data.discount
    
    # Create sale
    sale = Sale(
        client_id=client_id,
        client_name=client_name or "Client Anonyme",
        items=items,
        subtotal=subtotal,
        discount=sale_data.discount,
        total=total,
        payment_method=sale_data.payment_method
    )
    
    # Save to database
    sale_data_prepared = prepare_for_mongo(sale.dict())
    await db.sales.insert_one(sale_data_prepared)
    
    return sale

@api_router.get("/sales", response_model=List[Sale])
async def get_sales():
    sales = await db.sales.find().sort("created_at", -1).to_list(1000)
    return [Sale(**parse_from_mongo(sale)) for sale in sales]

@api_router.get("/sales/{sale_id}", response_model=Sale)
async def get_sale(sale_id: str):
    sale = await db.sales.find_one({"id": sale_id})
    if not sale:
        raise HTTPException(status_code=404, detail="Vente non trouvée")
    return Sale(**parse_from_mongo(sale))

# Dashboard endpoints
@api_router.get("/dashboard/stats")
async def get_dashboard_stats():
    # Get basic counts
    total_products = await db.products.count_documents({})
    total_clients = await db.clients.count_documents({})
    total_sales = await db.sales.count_documents({})
    
    # Get today's sales
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_sales = await db.sales.find({"created_at": {"$gte": today.isoformat()}}).to_list(1000)
    today_revenue = sum(sale.get("total", 0) for sale in today_sales)
    
    # Get low stock products (stock <= 5)
    low_stock_products = await db.products.find({"stock": {"$lte": 5}}).to_list(100)
    
    return {
        "total_products": total_products,
        "total_clients": total_clients,
        "total_sales": total_sales,
        "today_sales_count": len(today_sales),
        "today_revenue": today_revenue,
        "low_stock_count": len(low_stock_products),
        "low_stock_products": [Product(**parse_from_mongo(p)) for p in low_stock_products]
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()