import datetime
import re
import sqlite3
from contextlib import closing
from tempfile import NamedTemporaryFile

from epl_erratas.src.models import Book, Erratum, LibraryBase


class KoboLibrary(LibraryBase):
    """
    Library containing books and errata for Kobo eReaders.
    """

    def __init__(self, highlights: bytes):
        super(KoboLibrary, self).__init__(highlights)

        with NamedTemporaryFile(delete=False, suffix=self.highlights_format) as f:
            self._save_path = f.name
            f.write(highlights)

        self._load_books_from_db(self._save_path)

    @classmethod  # type: ignore
    @property
    def vendor(cls) -> str:
        return "Kobo"

    @classmethod  # type: ignore
    @property
    def upload_help(cls) -> str:
        return """
        Las anotaciones en los lectores Kobo se encuentran en la carpeta `/.kobo` en la raíz del lector.\n
        El archivo con las anotaciones se llama `KoboReader.sqlite`.
        """

    @classmethod  # type: ignore
    @property
    def highlights_format(cls) -> str:
        return "sqlite"

    def to_highlights(self) -> bytes:
        with open(self._save_path, "rb") as f:
            return f.read()

    def _load_books_from_db(self, db: str):
        """
        Load books and annotations from Kobo db.
        :param db: db file path
        """
        with sqlite3.connect(db) as con:
            with closing(con.cursor()) as cur:
                notes = cur.execute(
                    """
                    SELECT c.BookID, c.ContentID, c.BookTitle, c.Attribution, bm.Text, bm.Annotation, bm.DateCreated,
                           bm.BookmarkID
                    FROM Bookmark bm
                    INNER JOIN content c on bm.ContentID = c.ContentID
                    WHERE c.BookTitle NOT NULL
                    ORDER BY c.BookTitle
                    """,
                ).fetchall()

        self._books = dict()

        for (
            book_id,
            section,
            title,
            author,
            text,
            annotation,
            created_at,
            bm_id,
        ) in notes:
            if book_id not in self._books:
                self._books[book_id] = Book(book_id, title, author)

            # extract section if found
            if (match := re.search(r"[!/]Text/(.+)$", section)) is not None:
                section = match.group(1)

            self._books[book_id].add_erratum(
                Erratum(
                    id=bm_id,
                    highlight=text,
                    correction=annotation or text,
                    date=datetime.datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%f"),
                    section=section,
                ),
            )

    def _update_highlights(self, book: Book, errata: list[Erratum]):
        ids = ",".join(f"'{erratum.id}'" for erratum in errata)
        with sqlite3.connect(self._save_path) as con:
            with closing(con.cursor()) as cur:
                cur.execute(
                    f"""
                        DELETE FROM Bookmark
                        WHERE Bookmark.BookmarkID IN ({ids})
                        """,
                )
