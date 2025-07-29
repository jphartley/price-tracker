from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime
from pydantic import BaseModel
from scraper import PaulSmithScraper
import uvicorn

app = FastAPI(title="Price Tracker", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SQLALCHEMY_DATABASE_URL = "sqlite:///./price_tracker.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    current_price = Column(Float)  # Sale price or regular price if no sale
    original_price = Column(Float)  # Original/full price before discount
    currency = Column(String, default="GBP")
    created_at = Column(DateTime, default=datetime.utcnow)

class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), index=True)
    price = Column(Float)  # Current/sale price
    original_price = Column(Float)  # Original price if different from sale
    checked_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# Global scraper instance for browser reuse
scraper = PaulSmithScraper()

# Cleanup function for graceful shutdown
import atexit
import asyncio

def cleanup_scraper():
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Schedule cleanup for later if loop is running
            loop.create_task(scraper.close())
        else:
            # Run cleanup directly if no loop is running
            asyncio.run(scraper.close())
    except:
        pass  # Ignore cleanup errors

atexit.register(cleanup_scraper)

class ProductCreate(BaseModel):
    url: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "Price Tracker API"}

@app.get("/products")
async def get_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return products

@app.post("/products")
async def add_product(product: ProductCreate, db: Session = Depends(get_db)):
    # Check if product already exists
    existing = db.query(Product).filter(Product.url == product.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="Product already being tracked")
    
    # Scrape product info
    product_data = await scraper.scrape_product(product.url)
    if not product_data:
        raise HTTPException(status_code=400, detail="Could not scrape product information")
    
    if not product_data.get("name") or product_data.get("price") is None:
        raise HTTPException(status_code=400, detail="Invalid product data - missing name or price")
    
    # Create product record
    db_product = Product(
        url=product.url,
        name=product_data["name"],
        current_price=product_data["price"],
        original_price=product_data.get("original_price"),
        currency=product_data.get("currency", "GBP")
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    # Add initial price history
    price_record = PriceHistory(
        product_id=db_product.id,
        price=product_data["price"],
        original_price=product_data.get("original_price")
    )
    db.add(price_record)
    db.commit()
    
    return db_product

@app.post("/products/{product_id}/check-price")
async def check_price(product_id: int, db: Session = Depends(get_db)):
    # Get product
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Scrape current price
    product_data = await scraper.scrape_product(product.url)
    if not product_data:
        raise HTTPException(status_code=400, detail="Could not check price")
    
    new_price = product_data.get("price")
    if new_price is None:
        raise HTTPException(status_code=400, detail="Could not extract price from product page")
    
    # Update product current price, original price, and currency
    product.current_price = new_price
    product.original_price = product_data.get("original_price")
    product.currency = product_data.get("currency", product.currency)
    db.commit()
    
    # Add to price history
    price_record = PriceHistory(
        product_id=product_id,
        price=new_price,
        original_price=product_data.get("original_price")
    )
    db.add(price_record)
    db.commit()
    
    return {
        "product_id": product_id, 
        "new_price": new_price,
        "original_price": product_data.get("original_price"),
        "name": product.name, 
        "currency": product.currency
    }

@app.get("/products/{product_id}/history")
async def get_price_history(product_id: int, db: Session = Depends(get_db)):
    history = db.query(PriceHistory).filter(PriceHistory.product_id == product_id).order_by(PriceHistory.checked_at.desc()).all()
    return history

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)