"""Service for handling books operations."""

from src.app.models.book_model import BookModel


class BookService:
    """Service for managing books."""

    @staticmethod
    def create_book(data, admin_id):
        """Cria um novo livro."""
        book = BookModel(
            titulo=data.get("titulo"),
            autor=data.get("autor"),
            capa=data.get("capa"),
            idioma=data.get("idioma"),
            nivel=data.get("nivel"),
            genero=data.get("genero"),
            is_free=data.get("is_free", True),
            price=data.get("price"),
            payment_link=data.get("payment_link"),
            chapters=data.get("chapters", []),
            created_by=admin_id,
        )
        return book.save_to_db()

    @staticmethod
    def update_book(book_id, data):
        """Atualiza um livro existente."""
        book = BookModel.get_by_id(book_id)
        if not book:
            return None

        book_obj = BookModel(
            _id=book_id,
            titulo=data.get("titulo", book.get("titulo")),
            autor=data.get("autor", book.get("autor")),
            capa=data.get("capa", book.get("capa")),
            idioma=data.get("idioma", book.get("idioma")),
            nivel=data.get("nivel", book.get("nivel")),
            genero=data.get("genero", book.get("genero")),
            is_free=data.get("is_free", book.get("is_free")),
            price=data.get("price", book.get("price")),
            payment_link=data.get("payment_link", book.get("payment_link")),
            chapters=data.get("chapters", book.get("chapters", [])),
            created_at=book.get("created_at"),
        )
        return book_obj.update_to_db()

    @staticmethod
    def get_all_books():
        """Retorna todos os livros."""
        return BookModel.get_all()

    @staticmethod
    def get_available_books(user_id):
        """Retorna livros disponíveis e para descobrir."""
        return BookModel.get_available_books(user_id)

    @staticmethod
    def get_book_by_id(book_id):
        """Busca um livro pelo ID."""
        return BookModel.get_by_id(book_id)

    @staticmethod
    def delete_book(book_id):
        """Deleta um livro."""
        return BookModel.delete_book(book_id)

    @staticmethod
    def add_book_to_user(user_id, book_id):
        """Adiciona um livro à biblioteca do usuário."""
        BookModel.add_book_to_user(user_id, book_id)

