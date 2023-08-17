from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Smaller replicate of MPSConfig from SC_MPS_GUI


class MPSConfig:
    def __init__(self, filename=None):
        self.engine = create_engine(f"sqlite:///{filename}")
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
