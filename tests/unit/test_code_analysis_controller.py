import pytest
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_scan_code_text_invalid():
    from app.controllers.routes import code_analysis_controller
    with pytest.raises(HTTPException):
        await code_analysis_controller.scan_code_text({})


@pytest.mark.asyncio
async def test_scan_code_file_no_file():
    from app.controllers.routes import code_analysis_controller
    with pytest.raises(HTTPException):
        await code_analysis_controller.scan_code_file(None)
