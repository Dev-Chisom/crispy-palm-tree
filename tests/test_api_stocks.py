"""Tests for stock API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal, Base, engine
from app.models.stock import Stock, Market, AssetType

client = TestClient(app)


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_stock(db_session):
    """Create a sample stock for testing."""
    stock = Stock(
        symbol="TEST",
        name="Test Stock",
        market=Market.US,
        asset_type=AssetType.STOCK,
        currency="USD",
        is_active=True,
    )
    db_session.add(stock)
    db_session.commit()
    db_session.refresh(stock)
    return stock


def test_list_stocks_empty(db_session):
    """Test listing stocks when database is empty."""
    response = client.get("/api/v1/stocks")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total"] == 0
    assert len(data["data"]["items"]) == 0


def test_list_stocks_with_data(sample_stock):
    """Test listing stocks with data."""
    response = client.get("/api/v1/stocks")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total"] == 1
    assert len(data["data"]["items"]) == 1
    assert data["data"]["items"][0]["symbol"] == "TEST"


def test_get_stock_by_symbol(sample_stock):
    """Test getting a stock by symbol."""
    response = client.get("/api/v1/stocks/TEST")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["symbol"] == "TEST"
    assert data["data"]["name"] == "Test Stock"


def test_get_stock_by_id(sample_stock):
    """Test getting a stock by ID."""
    response = client.get(f"/api/v1/stocks/{sample_stock.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == sample_stock.id


def test_get_stock_not_found():
    """Test getting a non-existent stock."""
    response = client.get("/api/v1/stocks/NONEXISTENT")
    assert response.status_code == 404


def test_create_stock(db_session):
    """Test creating a new stock."""
    stock_data = {
        "symbol": "NEW",
        "name": "New Stock",
        "market": "US",
        "currency": "USD",
    }
    response = client.post("/api/v1/stocks", json=stock_data)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["symbol"] == "NEW"
    assert data["data"]["asset_type"] == "STOCK"  # Default


def test_create_stock_duplicate(sample_stock):
    """Test creating a duplicate stock."""
    stock_data = {
        "symbol": "TEST",
        "name": "Duplicate",
        "market": "US",
    }
    response = client.post("/api/v1/stocks", json=stock_data)
    assert response.status_code == 400


def test_filter_stocks_by_market(db_session):
    """Test filtering stocks by market."""
    # Create US stock
    us_stock = Stock(
        symbol="US1",
        name="US Stock",
        market=Market.US,
        asset_type=AssetType.STOCK,
        currency="USD",
        is_active=True,
    )
    # Create NGX stock
    ngx_stock = Stock(
        symbol="NGX1",
        name="NGX Stock",
        market=Market.NGX,
        asset_type=AssetType.STOCK,
        currency="NGN",
        is_active=True,
    )
    db_session.add(us_stock)
    db_session.add(ngx_stock)
    db_session.commit()
    
    # Test US filter
    response = client.get("/api/v1/stocks?market=US")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 1
    assert data["data"]["items"][0]["market"] == "US"
    
    # Test NGX filter
    response = client.get("/api/v1/stocks?market=NGX")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 1
    assert data["data"]["items"][0]["market"] == "NGX"


def test_filter_stocks_by_asset_type(db_session):
    """Test filtering stocks by asset type."""
    # Create stock
    stock = Stock(
        symbol="STOCK1",
        name="Stock",
        market=Market.US,
        asset_type=AssetType.STOCK,
        currency="USD",
        is_active=True,
    )
    # Create ETF
    etf = Stock(
        symbol="ETF1",
        name="ETF",
        market=Market.US,
        asset_type=AssetType.ETF,
        currency="USD",
        is_active=True,
    )
    db_session.add(stock)
    db_session.add(etf)
    db_session.commit()
    
    # Test ETF filter
    response = client.get("/api/v1/stocks?asset_type=ETF")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["total"] == 1
    assert data["data"]["items"][0]["asset_type"] == "ETF"
