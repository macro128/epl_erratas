import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterable

from epl_erratas import logger


@dataclass(repr=True)
class Erratum:
    """
    Single erratum information.
    """

    id: str = field(repr=False)
    highlight: str
    correction: str
    date: datetime.datetime
    position: int = -1
    section: str = ""


class Book:
    """
    Book containing errata information.
    """

    def __init__(
        self,
        id: str,
        title: str,
        author: str,
        errata: Iterable[Erratum] | None = None,
    ) -> None:
        self.id = id
        self.title = title
        self.author = author
        self._errata = {erratum.id: erratum for erratum in errata} if errata else dict()

    @property
    def errata(self) -> list[Erratum]:
        """
        List of book errata.
        :return: list
        """
        return list(self._errata.values())

    def add_erratum(self, erratum: Erratum):
        """
        Add erratum to book, if already exist then replace it.
        :param erratum: Erratum to add.
        """
        self._errata[erratum.id] = erratum

    def delete_erratum(self, erratum: Erratum):
        """
        Delete erratum from book, raise exception if not exist.
        :param erratum: Erratum to delete.
        """
        self._errata.pop(erratum.id)

    def __str__(self) -> str:
        r = self.title
        if self.author:
            r += f"({self.author})"
        return r

    def to_report(self, errata: list[Erratum] | None = None) -> str:
        """
        Generate report from book errata
        :param errata: list of book errata to use in report, if None use all
        :return: string report
        """
        _line = "## "
        _section = " || "
        _err = "\n<< "
        _correction = "\n>> "
        report = [
            "$$ Informe de erratas generado para ePLMulti (plugin de Sigil).",
            f"$$ Nombre: {self.title}",
            "$$ ",
            f"$$ Línea: {_line}",
            f"$$ Sección: {_section}",
            f"$$ Resalte: {_err}",
            f"$$ Nota: {_correction}",
            "$$ Final: ",
            "$$ \n",
        ]

        errata = errata or self.errata
        for erratum in errata:
            if erratum.id not in self._errata:
                logger.warning(f"{erratum} don't exist in {self}")
                continue
            report.append(
                f"{_line}{max(0, erratum.position)}"
                f'{_section}{erratum.section or "_"}'
                f"{_err}{erratum.highlight}"
                f"{_correction}{erratum.correction}"
                f"\n",
            )

        return "\n".join(report)

    def __len__(self) -> int:
        return len(self._errata)

    def __contains__(self, item):
        if not isinstance(item, Erratum):
            return False
        return item.id in self._errata


class LibraryBase(ABC):
    """
    Library containing books and errata.
    Must be implemented to load vendors' highlights.
    """

    def __init__(self, highlights: str):
        self._books: dict[str, Book] = dict()
        self._highlights = highlights

    @property
    def books(self) -> list[Book]:
        """
        List of library books.
        :return: list
        """
        return list(self._books.values())

    @classmethod  # type: ignore
    @property
    @abstractmethod
    def highlights_format(cls) -> str:
        """
        Allowed highlights file format.
        :return: str
        """
        pass

    @classmethod  # type: ignore
    @property
    @abstractmethod
    def vendor(cls) -> str:
        """
        eReader vendor
        :return: str
        """
        pass

    @classmethod  # type: ignore
    @property
    @abstractmethod
    def upload_help(cls) -> str:
        """
        File upload help.
        :return: str
        """
        pass

    @abstractmethod
    def _update_highlights(self, book: Book, errata: list[Erratum]):
        """
        Update original highlights deleting errata.
        :param book: library book
        :param errata: errata list to delete
        """
        pass

    def delete_errata(self, book: Book, errata: list[Erratum]):
        """
        Delete errata list from book in library and update highlights.
        :param book: library book
        :param errata: errata list to delete
        """
        if not errata:
            return
        if book.id not in self._books:
            raise LookupError(f"{book} not in library.")

        for erratum in errata:
            book.delete_erratum(erratum)

        if len(book) == 0:
            self._books.pop(book.id)

        self._update_highlights(book, errata)

    @abstractmethod
    def to_highlights(self) -> bytes:
        """
        Get updated highlights file
        :return: highlights bytes
        """
        return self._highlights.encode("utf-8")

    def __str__(self):
        return "Books:\n" + "\n".join(str(b) for b in self.books)
