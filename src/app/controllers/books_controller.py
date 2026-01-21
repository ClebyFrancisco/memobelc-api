"""Module for handling books-related endpoints."""

from flask import Blueprint, jsonify, request
from werkzeug.exceptions import BadRequest, Unauthorized
from src.app.services.books_service import BookService
from src.app.middlewares.token_required import token_required
from src.app import mongo
from bson import ObjectId


class BookController:
    """Class to handle books operations"""

    @staticmethod
    @token_required
    def create_book(current_user, token):
        """Cria um novo livro (apenas admin)."""
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        data = request.get_json()

        if "titulo" not in data:
            return jsonify({"error": "Missing required field: titulo"}), 400

        if "idioma" not in data:
            return jsonify({"error": "Missing required field: idioma"}), 400

        if "nivel" not in data:
            return jsonify({"error": "Missing required field: nivel"}), 400

        result = BookService.create_book(data, current_user._id)
        return jsonify(result), 201

    @staticmethod
    @token_required
    def update_book(current_user, token, book_id):
        """Atualiza um livro (apenas admin)."""
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        data = request.get_json()
        updated = BookService.update_book(book_id, data)

        if updated:
            return jsonify({"message": "Book updated successfully"}), 200
        return jsonify({"error": "Book not found"}), 404

    @staticmethod
    @token_required
    def delete_book(current_user, token, book_id):
        """Deleta um livro (apenas admin)."""
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        deleted = BookService.delete_book(book_id)

        if deleted:
            return jsonify({"message": "Book deleted successfully"}), 200
        return jsonify({"error": "Book not found"}), 404

    @staticmethod
    @token_required
    def get_all_books(current_user, token):
        """Retorna todos os livros (apenas admin para ver tudo)."""
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        books = BookService.get_all_books()
        return jsonify({"books": books}), 200

    @staticmethod
    @token_required
    def get_available_books(current_user, token):
        """Retorna livros do usuário e para descobrir."""
        result = BookService.get_available_books(current_user._id)
        return jsonify(result), 200

    @staticmethod
    @token_required
    def get_book_by_id(current_user, token, book_id):
        """Busca um livro pelo ID."""
        book = BookService.get_book_by_id(book_id)

        if not book:
            return jsonify({"error": "Book not found"}), 404

        # Verifica se o usuário tem acesso ao livro
        if not book.get("is_free"):
            from src.app import mongo
            from bson import ObjectId

            user_obj_id = ObjectId(current_user._id)
            book_obj_id = ObjectId(book_id)

            has_access = mongo.db.user_books.find_one({
                "user_id": user_obj_id,
                "book_id": book_obj_id,
            })

            if not has_access:
                return jsonify({"error": "Access denied. Book requires payment."}), 403

        return jsonify(book), 200

    @staticmethod
    @token_required
    def purchase_book(current_user, token):
        """Adiciona um livro à biblioteca do usuário após pagamento."""
        data = request.get_json()

        if "book_id" not in data:
            return jsonify({"error": "Missing book_id"}), 400

        book_id = data["book_id"]
        book = BookService.get_book_by_id(book_id)

        if not book:
            return jsonify({"error": "Book not found"}), 404

        # Se for gratuito ou se o usuário já pagou (verificado externamente), adiciona
        if book.get("is_free"):
            BookService.add_book_to_user(current_user._id, book_id)
            return jsonify({"message": "Book added to your library"}), 200
        else:
            # Para livros pagos, assumimos que o pagamento foi processado externamente
            # e o usuário está apenas confirmando
            BookService.add_book_to_user(current_user._id, book_id)
            return jsonify({"message": "Book purchased and added to your library"}), 200

    @staticmethod
    @token_required
    def admin_get_book_with_users(current_user, token, book_id):
        """Retorna detalhes do livro e lista de usuários com informação se possuem o livro (apenas admin)."""
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        book = BookService.get_book_by_id(book_id)
        if not book:
            return jsonify({"error": "Book not found"}), 404

        # Busca todos os usuários (id, nome, email)
        users_cursor = mongo.db.users.find({}, {"name": 1, "email": 1})
        users = []
        user_ids = []
        for u in users_cursor:
            uid = str(u["_id"])
            users.append(
                {
                    "_id": uid,
                    "name": u.get("name"),
                    "email": u.get("email"),
                }
            )
            user_ids.append(ObjectId(uid))

        # Busca quais usuários possuem o livro
        book_obj_id = ObjectId(book_id)
        user_books_cursor = mongo.db.user_books.find(
            {"book_id": book_obj_id, "user_id": {"$in": user_ids}}
        )
        users_with_book = {str(ub["user_id"]) for ub in user_books_cursor}

        # Marca flag has_book em cada usuário
        for u in users:
            u["has_book"] = u["_id"] in users_with_book

        return jsonify({"book": book, "users": users}), 200

    @staticmethod
    @token_required
    def admin_assign_book_to_user(current_user, token):
        """Atribui um livro a um usuário específico (apenas admin)."""
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        data = request.get_json()
        user_id = data.get("user_id")
        book_id = data.get("book_id")

        if not user_id or not book_id:
            return jsonify({"error": "Missing user_id or book_id"}), 400

        BookService.add_book_to_user(user_id, book_id)
        return jsonify({"message": "Book assigned to user"}), 200


# Blueprint para as rotas
books_blueprint = Blueprint("books_blueprint", __name__)

# Rotas admin
books_blueprint.route("/admin/create", methods=["POST"])(
    BookController.create_book
)
books_blueprint.route("/admin/update/<string:book_id>", methods=["PUT"])(
    BookController.update_book
)
books_blueprint.route("/admin/delete/<string:book_id>", methods=["DELETE"])(
    BookController.delete_book
)
books_blueprint.route("/admin/list", methods=["GET"])(
    BookController.get_all_books
)
books_blueprint.route("/admin/book/<string:book_id>", methods=["GET"])(
    BookController.admin_get_book_with_users
)
books_blueprint.route("/admin/assign", methods=["POST"])(
    BookController.admin_assign_book_to_user
)

# Rotas usuário
books_blueprint.route("/list", methods=["GET"])(
    BookController.get_available_books
)
books_blueprint.route("/get/<string:book_id>", methods=["GET"])(
    BookController.get_book_by_id
)
books_blueprint.route("/purchase", methods=["POST"])(
    BookController.purchase_book
)