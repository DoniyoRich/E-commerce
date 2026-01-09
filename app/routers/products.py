from typing import Any, Coroutine

from fastapi import APIRouter, status, HTTPException, Depends

from app.models import Product as ProductTable, Category as CategoryTable
from app.schemas import Product as ProductResponse, ProductCreate
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from app.db_depends import get_db

# Создаем маршрутизатор для товаров
router = APIRouter(
    prefix="/products",
    tags=["products"],
)


@router.get("/", response_model=list[ProductResponse], status_code=200)
async def get_all_active_products(db: Session = Depends(get_db)):
    """
    Возвращает список всех активных товаров.
    """

    products = db.scalars(
        select(ProductTable)
        .join(CategoryTable)
        .where(
            ProductTable.is_active == True,
            CategoryTable.is_active == True,
            ProductTable.stock > 0,
        )
    ).all()

    return products


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """
    Создает новый товар.
    """
    category = db.get(CategoryTable, product.category_id)

    if not category:
        raise HTTPException(
            status_code=404, detail=f"Category with id {product.category_id} not found"
        )

    if not category.is_active:
        raise HTTPException(
            status_code=400, detail=f"Category '{category.name}' is inactive"
        )

    # Создание нового товара
    # преобразуем (model_dump) Pydantic модель product в словарь, распакуем параметры (**)
    # и создадим SQLAlchemy модель db_product
    db_product = ProductTable(**product.model_dump())

    # добавляем в сессию db, но пока НЕ записываем. Alchemy его отслеживает, как stage (индекс) в git
    db.add(db_product)

    # вот теперь идет запись в БД, а именно INSERT ....
    db.commit()

    # Обновляем саму модель Product в контексте Python, т.е. получаем, например, обновленный id.
    db.refresh(db_product)

    return db_product


@router.get(
    "/category/{category_id}", response_model=list[ProductResponse], status_code=200
)
async def get_products_by_category(category_id: int, db: Session = Depends(get_db)):
    """
    Возвращает список товаров в указанной категории по ее ID.
    """
    category = db.scalars(
        select(CategoryTable).where(
            CategoryTable.id == category_id, CategoryTable.is_active == True
        )
    ).one_or_none()

    # category = db.get(CategoryTable, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found or inactive")

    active_products = [product for product in category.products if product.is_active]

    return active_products


@router.get("/{product_id}", response_model=ProductResponse, status_code=200)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    Возвращает детальную информацию о товаре по его ID.
    """
    # Один запрос с JOIN и проверкой активности категории
    stmt = (
        select(ProductTable)
        .join(CategoryTable, ProductTable.category_id == CategoryTable.id)
        .where(
            ProductTable.id == product_id,
            ProductTable.is_active == True,
            CategoryTable.is_active == True  # Проверяем активность категории
        )
    )

    product = db.scalars(stmt).one_or_none()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found, inactive, or its category is inactive"
        )

    return product


@router.put("/{product_id}", response_model=ProductResponse, status_code=200)
async def update_product(product_id: int, product_upd: ProductCreate, db: Session = Depends(get_db)):
    """
    Обновляет товар по его ID.
    """
    # Находим продукт
    product = db.get(ProductTable, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Получаем данные для обновления
    update_data = product_upd.model_dump(exclude_unset=True)

    # Если нет данных для обновления
    if not update_data:
        return product

    # Проверяем категорию, если она меняется
    if "category_id" in update_data:
        category = db.get(CategoryTable, update_data["category_id"])
    else:
        # Используем текущую категорию продукта
        category = db.get(CategoryTable, product.category_id)

    if not category or not category.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found or inactive"
        )

    # Выполняем обновление
    db.execute(
        update(ProductTable)
        .where(ProductTable.id == product_id)
        .values(**update_data)
    )
    db.commit()

    # Получаем обновленный продукт
    db.refresh(product)

    return product


@router.delete("/{product_id}", status_code=200)
async def delete_product(product_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    """
    Логически удаляет товар по его ID.
    """

    stmt = select(ProductTable).where(ProductTable.id == product_id, ProductTable.is_active == True)
    product = db.scalars(stmt).one_or_none()

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    product.is_active = False

    db.commit()

    return {"status": "success", "message": "Product marked as inactive"}
