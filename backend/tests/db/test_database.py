import pytest
from backend.db.database import init_db, engine
from backend.db.models import Base

def test_init_db_success(mocker):
    # Mock Base.metadata.create_all
    mock_create_all = mocker.patch.object(Base.metadata, 'create_all')
    # Mock logger.info
    mock_logger_info = mocker.patch('backend.db.database.logger.info')

    # Call the function
    init_db()

    # Assertions
    mock_create_all.assert_called_once_with(bind=engine)
    mock_logger_info.assert_called_once_with("Database tables created successfully.")

def test_init_db_exception(mocker):
    # Mock Base.metadata.create_all to raise an exception
    test_exception = Exception("Test DB creation error")
    mock_create_all = mocker.patch.object(Base.metadata, 'create_all', side_effect=test_exception)
    # Mock logger.error
    mock_logger_error = mocker.patch('backend.db.database.logger.error')

    # Call the function and expect the exception
    with pytest.raises(Exception) as exc_info:
        init_db()

    # Assertions
    assert str(exc_info.value) == "Test DB creation error"
    mock_create_all.assert_called_once_with(bind=engine)
    mock_logger_error.assert_called_once_with(f"Error creating database tables: {test_exception}")
