from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.categories import Category as CategoryModel
from app.schemas import Category as CategorySchema, CategoryCreate
from app.db_depends import get_db

# Создаем маршрутизатор с префиксом и тэгом
router = APIRouter(
    prefix="/categories",
    tags=["categories"],
)


@router.get("/")
async def get_all_categories():
    """
    Возвращает список всех категорий товаров.
    """
    return {"message": "Список всех категорий (заглушка)"}


@router.post("/", response_model=CategorySchema, status_code=status.HTTP_201_CREATED)
async def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    """
    Создает новую категорию.
    """
    # Проверка существования parent_id, если указан
    if category.parent_id is not None:
        stmt = select(CategoryModel).where(
            CategoryModel.id == category.parent_id,
            CategoryModel.is_active == True)
        parent = db.scalars(stmt).first()
        if parent is None:
            raise HTTPException(status_code=400, detail="Parent category not found")

    # Создание новой категории
    # преобразуем (model_dump) Pydantic модель category в словарь, распакуем параметры (**)
    # и создадим SQLAlchemy модель db_category
    db_category = CategoryModel(**category.model_dump())

    # добавляем в сессию db, но пока НЕ записываем. Alchemy его отслеживает, как stage (индекс) в git
    db.add(db_category)

    # вот теперь идет запись в БД, а именно INSERT ....
    db.commit()

    # Обновляем саму модель Category в контексте Python, т.е. получаем например обновленный id.
    db.refresh(db_category)

    return db_category


@router.put("/{category_id}")
async def update_category(category_id: int):
    """
    Обновляет категорию по ее ID.
    """
    return {"message": f"Категория с ID {category_id} обновлена (заглушка)"}


@router.delete("/{category_id}")
async def delete_category(category_id: int):
    """
    Удаляет категорию по ее ID.
    """
    return {"message": f"Категория с ID {category_id} удалена (заглушка)"}
