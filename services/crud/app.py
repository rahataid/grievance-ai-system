from typing import Optional
 
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
 
from shared.database.models import App

 
async def get_app(db: AsyncSession, app_id: str) -> Optional[App]:
    result = await db.execute(select(App).where(App.id == app_id))
    return result.scalar_one_or_none()
 
 
async def get_all_apps(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[App]:
    result = await db.execute(select(App).offset(skip).limit(limit))
    return result.scalars().all()
 
 
async def update_app(
    db: AsyncSession,
    app_id: str,
    name: Optional[str] = None,
    email: Optional[str] = None,
    is_verified: Optional[bool] = None,
) -> Optional[App]:
    app = await get_app(db, app_id)
    if not app:
        return None
 
    if name is not None:
        app.name = name
    if email is not None:
        app.email = email
    if is_verified is not None:
        app.is_verified = is_verified
 
    await db.commit()
    await db.refresh(app)
    return app
 
 
async def delete_app(db: AsyncSession, app_id: str) -> bool:
    app = await get_app(db, app_id)
    if not app:
        return False
    await db.delete(app)
    await db.commit()
    return True