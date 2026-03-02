import os
import sys
from colorama import init, Fore, Style
from src.document_processor import load_and_chunk_pdfs
from src.vector_db import ingest_chunks, get_collection_stats
from src.cli import run
from src.config import DATA_DIR

init(autoreset=True)

WELCOME = f"""
{Fore.GREEN}{Style.BRIGHT}╔══════════════════════════════════════════════╗
║     Jäppinen Ltd. - Technical Support AI     ║
║     Maytag & Midea Service Manual Assistant  ║
╚══════════════════════════════════════════════╝{Style.RESET_ALL}

Ask any question about the Maytag or Midea service manuals.
Type {Fore.CYAN}/help{Style.RESET_ALL} for available commands. Type {Fore.CYAN}quit{Style.RESET_ALL} or {Fore.CYAN}exit{Style.RESET_ALL} to close.
"""


def bootstrap() -> None:
    """Ingest PDFs into the vector store if not already done."""
    if not os.path.isdir(DATA_DIR) or not any(f.endswith(".pdf") for f in os.listdir(DATA_DIR)):
        print(Fore.RED + f"Error: no PDF manuals found in '{DATA_DIR}/'.")
        print(Fore.RED + "Add the service manual PDF files to that directory and restart.")
        sys.exit(1)

    from src.vector_db import _get_collection
    collection = _get_collection()

    if collection.count() > 0:
        stats = get_collection_stats()
        print(Fore.GREEN + f"Vector store ready - {len(stats)} manual(s) loaded:")
        for source, count in sorted(stats.items()):
            print(Fore.GREEN + f"  • {source}  -  {count} chunks")
        print()
        return

    print(Fore.YELLOW + "First run - loading and indexing documentation. This may take a minute...")
    chunks = load_and_chunk_pdfs()
    ingest_chunks(chunks)
    print(Fore.GREEN + "Indexing complete.\n")


if __name__ == "__main__":
    print(WELCOME)
    bootstrap()
    run()