from passlib.context import CryptContext

# Создаем контекст для хэширования с использованием bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Преобразует пароль в хэш с использованием bcrypt.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет, соответствует ли введенный пароль сохраненному хэшу.
    """
    return pwd_context.verify(plain_password, hashed_password)
