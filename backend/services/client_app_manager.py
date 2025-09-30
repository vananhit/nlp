import uuid
import secrets
from sqlalchemy.orm import Session
from backend.models.client_app import ClientApp
from backend.security import get_password_hash, verify_password

class ClientAppManager:
    def create_client_app(self, db: Session, name: str):
        client_id = str(uuid.uuid4())
        client_secret = secrets.token_urlsafe(32)
        
        hashed_secret = get_password_hash(client_secret)
        
        db_client_app = ClientApp(
            name=name,
            client_id=client_id,
            hashed_secret=hashed_secret
        )
        
        db.add(db_client_app)
        db.commit()
        db.refresh(db_client_app)
        
        # Return the raw secret only at creation time
        return db_client_app, client_secret

    def get_client_apps(self, db: Session):
        return db.query(ClientApp).all()

    def delete_client_app(self, db: Session, client_id: str):
        db_client_app = db.query(ClientApp).filter(ClientApp.client_id == client_id).first()
        if db_client_app:
            db.delete(db_client_app)
            db.commit()
        return db_client_app

    def authenticate_client(self, db: Session, client_id: str, client_secret: str) -> ClientApp | None:
        db_client_app = db.query(ClientApp).filter(ClientApp.client_id == client_id).first()
        if not db_client_app:
            return None
        if not verify_password(client_secret, db_client_app.hashed_secret):
            return None
        return db_client_app

client_app_manager = ClientAppManager()
