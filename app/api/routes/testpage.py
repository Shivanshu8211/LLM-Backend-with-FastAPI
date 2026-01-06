from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def test_page():
    return {"message": "This is a test page"}

@router.get("/info")
def test_info():
    return {"info": "This is some test information"}