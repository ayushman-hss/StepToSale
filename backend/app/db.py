from sqlmodel import SQLModel, create_engine, Session
from .config import settings

engine = create_engine(settings.database_url, echo=False, pool_pre_ping=True)

def init_db() -> None:
    # Import models so SQLModel sees them before create_all
    from . import models  # noqa: F401
    from . import models_pooling  # noqa: F401
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session