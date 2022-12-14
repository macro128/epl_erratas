import streamlit as st

try:
    from epl_erratas.src.libraries import KoboLibrary
except ModuleNotFoundError:
    import os
    from pathlib import Path

    _python_path = os.getenv("PYTHONPATH", "")
    os.environ["PYTHONPATH"] = f"{Path(__file__).parent.absolute()}:{_python_path}"
    from epl_erratas.src.libraries import KoboLibrary

from epl_erratas.src.models import Book, Erratum

AVAILABLE_LIBRARIES = {lib.highlights_format: lib for lib in [KoboLibrary]}


def write_erratum(erratum: Erratum):
    _, col0, col1, col2, _ = st.columns([0.5, 1.5, 8, 8, 1])
    with col0:
        st.write("\n")
        st.checkbox("", key=erratum, help="Desmarcar para omitir anotación en reporte")
    with col1:
        st.markdown(f"**Errata**\n\n{erratum.highlight}")
    with col2:
        erratum.correction = st.text_area(
            "Corrección",
            erratum.correction,
            height=int(len(erratum.highlight) * 0.6),
        ).strip()

    _, col1, col2, _ = st.columns([2, 8, 8, 1])
    with col1:
        if erratum.position > -1:
            st.markdown(f"**Posición**\n\n{erratum.position}")
        if erratum.section:
            st.markdown(f"**Sección**\n\n{erratum.section}")
    with col2:
        st.markdown(f"**Fecha**\n\n{erratum.date}")

    st.markdown("---")


def main():
    st.title("📚 ePL Erratas")

    st.sidebar.header("Biblioteca")

    file = st.sidebar.file_uploader(
        "Selecciona el archivo de las anotaciones",
        type=list(AVAILABLE_LIBRARIES),
    )
    if file is None:
        st.session_state.library = None
        st.session_state.updated = False
        st.warning("⭕️ No has seleccionado un archivo de anotaciones")
        for i, lib in enumerate(AVAILABLE_LIBRARIES.values()):
            with st.expander(f"Lectores {lib.vendor}", expanded=i == 0):
                st.markdown(lib.upload_help)
        st.stop()

    if st.session_state.get("library", None) is None:
        try:
            st.session_state.library = AVAILABLE_LIBRARIES[file.name.split(".")[-1]](
                file.getvalue(),
            )
        except Exception as e:
            st.error("**Error cargando archivo de anotaciones**")
            with st.expander("Más información", expanded=False):
                st.exception(e)
            st.stop()

    library = st.session_state.library

    if not (books := list(library.books)):
        st.warning("El archivo seleccionado no contiene anotaciones")
        st.stop()

    book: Book = st.sidebar.selectbox("Selecciona un libro", books)
    st.sidebar.subheader("Opciones del libro")
    sort_options = {
        "Fecha de creación": "date",
        "Posición": "position",
        "Sección": "section",
    }
    sort_by = sort_options[st.sidebar.selectbox("Ordenar por", sort_options)]

    has_corrections = False
    st.header(book.title)
    if book.author:
        st.markdown(f"Por **{book.author}**")

    st.markdown(
        "**Corrige** las erratas, "
        "**selecciona** las anotaciones a reportar y **genera** el reporte.✏️️✔️💾",
    )

    report_place_holder = st.empty()
    errata, hidden_errata = [], []
    for erratum in sorted(book.errata, key=lambda e: getattr(e, sort_by, "")):
        if st.session_state.setdefault(erratum, True):
            errata.append(erratum)
        else:
            hidden_errata.append(erratum)

    if errata:
        st.markdown("---")
        for erratum in errata:
            write_erratum(erratum)
            if erratum.correction:
                has_corrections = True

    if hidden_errata:
        with st.expander("Anotaciones omitidas"):
            st.markdown("---")
            for erratum in hidden_errata:
                write_erratum(erratum)

    if has_corrections:
        if st.sidebar.button("Generar reporte", type="primary"):
            with report_place_holder.expander("Reporte de erratas", expanded=True):
                st.code(book.to_report(errata))

    if errata:
        if st.sidebar.button("Eliminar erratas seleccionadas"):
            library.delete_errata(book, errata)
            st.session_state.updated = True
            st.experimental_rerun()

    if st.session_state.get("updated", False):
        st.sidebar.download_button(
            "Descargar anotaciones actualizadas",
            data=library.to_highlights(),
            file_name=file.name,
            help="Descarga el archivo de anotaciones sin las eliminadas",
        )


if __name__ == "__main__":
    st.set_page_config("EPL Erratas", ":book:", layout="wide")
    main()
