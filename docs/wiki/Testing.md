# Testing

Running and writing tests for ImageMagick WebGUI.

---

## Overview

The project includes:
- Backend unit tests (pytest)
- API integration tests
- Frontend component tests (optional)

---

## Running Tests

### Backend Tests

```bash
# Enter backend directory
cd backend

# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_main.py

# Run specific test
pytest tests/test_main.py::test_health_check

# Run with coverage
pytest --cov=app --cov-report=html
```

### Docker Test Environment

```bash
# Run tests in Docker
docker compose exec app pytest

# Or build test container
docker compose -f docker-compose.test.yml up --build
```

---

## Test Structure

```
backend/
└── tests/
    ├── __init__.py
    ├── conftest.py          # Fixtures
    ├── test_main.py         # Main app tests
    ├── test_auth.py         # Auth tests
    ├── test_images.py       # Image API tests
    ├── test_operations.py   # Operations tests
    └── test_services/
        ├── test_imagemagick.py
        └── test_file_service.py
```

---

## Test Examples

### Health Check Test

```python
# tests/test_main.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
```

### Authentication Tests

```python
# tests/test_auth.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_user(client):
    response = await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "testpassword123",
        "name": "Test User"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

@pytest.mark.asyncio
async def test_login(client, test_user):
    response = await client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "testpassword123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_login_invalid_password(client, test_user):
    response = await client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
```

### Image Upload Tests

```python
# tests/test_images.py
import pytest
from pathlib import Path

@pytest.mark.asyncio
async def test_upload_image(client, auth_headers, sample_image):
    with open(sample_image, "rb") as f:
        response = await client.post(
            "/api/images/upload",
            files={"files": ("test.jpg", f, "image/jpeg")},
            headers=auth_headers
        )
    assert response.status_code == 200
    data = response.json()
    assert len(data["images"]) == 1

@pytest.mark.asyncio
async def test_upload_invalid_file(client, auth_headers):
    response = await client.post(
        "/api/images/upload",
        files={"files": ("test.exe", b"fake", "application/octet-stream")},
        headers=auth_headers
    )
    assert response.status_code == 400
```

### ImageMagick Service Tests

```python
# tests/test_services/test_imagemagick.py
import pytest
from app.services.imagemagick import imagemagick_service

@pytest.mark.asyncio
async def test_build_resize_command():
    command = await imagemagick_service.build_command(
        "/tmp/input.jpg",
        "/tmp/output.jpg",
        [{"operation": "resize", "params": {"width": 800, "height": 600}}]
    )
    assert "-resize" in command
    assert "800x600" in command

@pytest.mark.asyncio
async def test_validate_allowed_operation():
    assert imagemagick_service.is_allowed("resize") == True
    assert imagemagick_service.is_allowed("rm") == False

@pytest.mark.asyncio
async def test_execute_with_timeout(sample_image):
    command = f"magick {sample_image} -resize 100x100 /tmp/out.jpg"
    success, stdout, stderr = await imagemagick_service.execute(command)
    assert success == True
```

---

## Test Fixtures

### conftest.py

```python
# tests/conftest.py
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.main import app
from app.core.database import get_db
from app.models import Base

# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSession(engine) as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

@pytest.fixture
async def test_user(client):
    response = await client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "testpassword123"
    })
    return response.json()

@pytest.fixture
def auth_headers(test_user):
    return {"Authorization": f"Bearer {test_user['access_token']}"}

@pytest.fixture
def sample_image(tmp_path):
    # Create a simple test image
    from PIL import Image
    img = Image.new("RGB", (100, 100), color="red")
    path = tmp_path / "test.jpg"
    img.save(path)
    return path
```

---

## Writing Tests

### Best Practices

1. **Isolate tests** - Each test independent
2. **Use fixtures** - Share setup code
3. **Test edge cases** - Invalid inputs, errors
4. **Mock external services** - Don't call real APIs
5. **Async tests** - Use `@pytest.mark.asyncio`

### Test Categories

| Category | What to Test |
|----------|--------------|
| Unit | Individual functions |
| Integration | API endpoints |
| Service | Business logic |
| Security | Auth, validation |

### Naming Convention

```python
def test_<what>_<condition>_<expected>():
    # test_upload_image_success
    # test_upload_invalid_file_returns_400
    # test_resize_preserves_aspect_ratio
```

---

## Coverage

### Generate Coverage Report

```bash
# Run with coverage
pytest --cov=app --cov-report=html

# Open report
open htmlcov/index.html
```

### Coverage Targets

| Component | Target |
|-----------|--------|
| API routes | 80%+ |
| Services | 90%+ |
| Models | 70%+ |
| Utils | 90%+ |

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      
      - name: Run tests
        run: |
          cd backend
          pytest --cov=app
```

---

## Troubleshooting Tests

### Common Issues

**Database not found:**
```bash
# Ensure test DB is created
pytest --setup-show
```

**Async errors:**
```python
# Add to conftest.py
import pytest_asyncio
pytest_plugins = ('pytest_asyncio',)
```

**Import errors:**
```bash
# Install in dev mode
pip install -e .
```

**Flaky tests:**
- Check for race conditions
- Use proper async handling
- Isolate test data

---

## Next Steps

- [[Architecture]] - System design
- [[Contributing]] - How to contribute
- [[Deployment]] - Production setup
