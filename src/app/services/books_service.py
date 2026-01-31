"""Service for handling books operations."""

from bson import ObjectId
from src.app.models.book_model import BookModel
from src.app.models.collection_model import CollectionModel
from src.app.models.deck_model import DeckModel
from src.app.models.user_model import UserModel
from src.app.models.user_progress_model import UserProgressModel


class BookService:
    """Service for managing books."""

    @staticmethod
    def create_book(data, admin_id):
        """Cria um novo livro: gera uma collection com nome e imagem do livro e um deck por capítulo."""
        titulo = data.get("titulo")
        capa = data.get("capa")

        # Cria collection do livro (sem user = collection do sistema)
        collection = CollectionModel(name=titulo, image=capa)
        result = collection.save_to_db()
        collection_id = result["collection_id"]

        # Para cada capítulo, cria um deck na collection e preserva pdf_url, images_urls, audio_url, ordem, titulo
        chapters_with_decks = []
        for ch in data.get("chapters", []):
            chapter_title = ch.get("title") or ch.get("titulo") or "Chapter"
            deck = DeckModel(
                name=chapter_title,
                collection_id=collection_id,
                image=capa,
            )
            deck_id = deck.save_to_db()
            chapter_data = {
                "titulo": ch.get("titulo") or ch.get("title") or chapter_title,
                "title": chapter_title,
                "content": ch.get("content") or ch.get("conteudo") or "",
                "ordem": ch.get("ordem", len(chapters_with_decks) + 1),
                "pdf_url": ch.get("pdf_url") or "",
                "images_urls": ch.get("images_urls") or [],
                "audio_url": ch.get("audio_url") or "",
                "deck_id": deck_id,
            }
            chapters_with_decks.append(chapter_data)

        book = BookModel(
            titulo=titulo,
            autor=data.get("autor"),
            capa=capa,
            idioma=data.get("idioma"),
            nivel=data.get("nivel"),
            genero=data.get("genero"),
            is_free=data.get("is_free", True),
            price=data.get("price"),
            payment_link=data.get("payment_link"),
            chapters=chapters_with_decks,
            collection_id=collection_id,
            created_by=admin_id,
        )
        return book.save_to_db()

    @staticmethod
    def update_book(book_id, data):
        """Atualiza um livro existente. Novos capítulos (sem deck_id) ganham um deck na collection do livro."""
        book = BookModel.get_by_id(book_id)
        if not book:
            return None

        chapters = data.get("chapters", book.get("chapters", []))
        collection_id = book.get("collection_id")
        capa = data.get("capa") or book.get("capa")

        # Para capítulos existentes (com deck_id) preserva todos os campos; para novos cria deck
        chapters_with_decks = []
        for idx, ch in enumerate(chapters):
            if ch.get("deck_id"):
                # Mantém campos do app: titulo, ordem, pdf_url, images_urls, audio_url
                merged = dict(ch)
                merged["titulo"] = ch.get("titulo") or ch.get("title") or ""
                merged["ordem"] = ch.get("ordem", idx + 1)
                merged["pdf_url"] = ch.get("pdf_url") or ""
                merged["images_urls"] = ch.get("images_urls") or []
                merged["audio_url"] = ch.get("audio_url") or ""
                chapters_with_decks.append(merged)
                continue
            chapter_title = ch.get("title") or ch.get("titulo") or "Chapter"
            deck = DeckModel(
                name=chapter_title,
                collection_id=collection_id,
                image=capa,
            )
            deck_id = deck.save_to_db()
            chapter_data = {
                "titulo": ch.get("titulo") or ch.get("title") or chapter_title,
                "title": chapter_title,
                "content": ch.get("content") or ch.get("conteudo") or "",
                "ordem": ch.get("ordem", idx + 1),
                "pdf_url": ch.get("pdf_url") or "",
                "images_urls": ch.get("images_urls") or [],
                "audio_url": ch.get("audio_url") or "",
                "deck_id": deck_id,
            }
            chapters_with_decks.append(chapter_data)

        book_obj = BookModel(
            _id=book_id,
            titulo=data.get("titulo", book.get("titulo")),
            autor=data.get("autor", book.get("autor")),
            capa=capa,
            idioma=data.get("idioma", book.get("idioma")),
            nivel=data.get("nivel", book.get("nivel")),
            genero=data.get("genero", book.get("genero")),
            is_free=data.get("is_free", book.get("is_free")),
            price=data.get("price", book.get("price")),
            payment_link=data.get("payment_link", book.get("payment_link")),
            chapters=chapters_with_decks,
            collection_id=collection_id,
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
    def get_book_by_id_for_user(book_id, user_id):
        """Busca um livro pelo ID com flags por capítulo: has_cards e user_has_saved."""
        book = BookModel.get_by_id(book_id)
        if not book:
            return None
        chapters = book.get("chapters", [])
        enriched = []
        for ch in chapters:
            deck_id = ch.get("deck_id")
            if not deck_id:
                enriched.append({**ch, "deck_id": None, "has_cards": False, "user_has_saved": False})
                continue
            deck = DeckModel.get_by_id(deck_id)
            cards_count = len(deck.get("cards", [])) if deck else 0
            has_cards = cards_count > 0
            user_has_saved = (
                DeckModel.check_if_the_user_has_the_deck(user_id, deck_id).get("user_has_deck") == "true"
            )
            enriched.append({
                **ch,
                "deck_id": deck_id,
                "has_cards": has_cards,
                "user_has_saved": user_has_saved,
            })
        book = dict(book)
        book["chapters"] = enriched
        return book

    @staticmethod
    def generate_collection_for_book(book_id):
        """Gera collection e decks para um livro que ainda não tem collection_id (livros criados antes da atualização)."""
        book = BookModel.get_by_id(book_id)
        if not book:
            return None
        if book.get("collection_id"):
            return {"already": True, "collection_id": book.get("collection_id")}

        titulo = book.get("titulo") or "Book"
        capa = book.get("capa")

        collection = CollectionModel(name=titulo, image=capa)
        result = collection.save_to_db()
        collection_id = result["collection_id"]

        chapters_with_decks = []
        for idx, ch in enumerate(book.get("chapters", [])):
            chapter_title = ch.get("title") or ch.get("titulo") or "Chapter"
            deck = DeckModel(
                name=chapter_title,
                collection_id=collection_id,
                image=capa,
            )
            deck_id = deck.save_to_db()
            chapter_data = dict(ch)
            chapter_data["titulo"] = ch.get("titulo") or ch.get("title") or chapter_title
            chapter_data["title"] = chapter_title
            chapter_data["ordem"] = ch.get("ordem", idx + 1)
            chapter_data["deck_id"] = deck_id
            chapter_data.setdefault("pdf_url", "")
            chapter_data.setdefault("images_urls", [])
            chapter_data.setdefault("audio_url", "")
            chapter_data.setdefault("content", "")
            chapters_with_decks.append(chapter_data)

        book_obj = BookModel(
            _id=book_id,
            titulo=titulo,
            autor=book.get("autor"),
            capa=capa,
            idioma=book.get("idioma"),
            nivel=book.get("nivel"),
            genero=book.get("genero"),
            is_free=book.get("is_free"),
            price=book.get("price"),
            payment_link=book.get("payment_link"),
            chapters=chapters_with_decks,
            collection_id=collection_id,
            created_at=book.get("created_at"),
        )
        book_obj.update_to_db()
        return {"collection_id": collection_id, "message": "Collection and decks generated"}

    @staticmethod
    def add_chapter(book_id, title, content=None):
        """Adiciona um capítulo ao livro: cria um deck na collection do livro."""
        book = BookModel.get_by_id(book_id)
        if not book:
            return None
        collection_id = book.get("collection_id")
        if not collection_id:
            return None
        deck = DeckModel(
            name=title or "Chapter",
            collection_id=collection_id,
            image=book.get("capa"),
        )
        deck_id = deck.save_to_db()
        chapters = list(book.get("chapters", []))
        chapters.append({
            "title": title or "Chapter",
            "content": content or "",
            "deck_id": deck_id,
        })
        book_obj = BookModel(
            _id=book_id,
            titulo=book.get("titulo"),
            autor=book.get("autor"),
            capa=book.get("capa"),
            idioma=book.get("idioma"),
            nivel=book.get("nivel"),
            genero=book.get("genero"),
            is_free=book.get("is_free"),
            price=book.get("price"),
            payment_link=book.get("payment_link"),
            chapters=chapters,
            collection_id=collection_id,
            created_at=book.get("created_at"),
        )
        book_obj.update_to_db()
        return {"deck_id": deck_id, "chapter": chapters[-1]}

    @staticmethod
    def add_cards_to_chapter(book_id, deck_id, card_ids):
        """Admin: adiciona cartas ao deck do capítulo (deck deve pertencer ao livro)."""
        book = BookModel.get_by_id(book_id)
        if not book:
            return False
        for ch in book.get("chapters", []):
            if ch.get("deck_id") == deck_id:
                DeckModel.add_cards_to_deck(deck_id, card_ids)
                return True
        return False

    @staticmethod
    def save_chapter_cards(user_id, book_id, deck_id):
        """Usuário salva as cartas do capítulo: cria/usa collection do livro para o user e gera progresso."""
        book = BookModel.get_by_id(book_id)
        if not book:
            return None
        # Confere se o deck pertence ao livro
        if not any(ch.get("deck_id") == deck_id for ch in book.get("chapters", [])):
            return None
        deck = DeckModel.get_by_id(deck_id)
        if not deck or not deck.get("cards"):
            return {"message": "No cards to save", "collection_id": None}

        # Obtém ou cria a collection do usuário para este livro
        user_coll = CollectionModel.get_user_collection_by_book_id(user_id, book_id)
        if user_coll:
            collection_id = user_coll["_id"]
        else:
            new_coll = CollectionModel(
                name=book.get("titulo"),
                image=book.get("capa"),
                book_id=book_id,
                user=user_id,
            )
            result = new_coll.save_to_db()
            collection_id = result["collection_id"]

        CollectionModel.add_decks_to_collection(collection_id, [deck_id])
        # Se a collection foi criada agora, save_to_db já a adicionou ao user

        for card_id in deck.get("cards", []):
            UserProgressModel.create_or_update(user_id, deck_id, str(card_id))

        return {"message": "Chapter cards saved", "collection_id": collection_id}

    @staticmethod
    def delete_book(book_id):
        """Deleta um livro."""
        return BookModel.delete_book(book_id)

    @staticmethod
    def add_book_to_user(user_id, book_id):
        """Adiciona um livro à biblioteca do usuário."""
        BookModel.add_book_to_user(user_id, book_id)

