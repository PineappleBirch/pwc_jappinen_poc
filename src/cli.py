import readline  # noqa: F401 - activates up/down history and left/right cursor navigation in input()
from colorama import init, Fore, Style
from src.rag_engine import query_stream
from src.logger import log_query
from src.vector_db import get_collection_stats
from src.config import CONFIDENCE_THRESHOLD, HISTORY_WINDOW

init(autoreset=True)

MANUAL_ALIASES = {
    "maytag": "technical-manual-w11663204-revb.pdf",
    "midea":  "LAD-Front-Loading-Service-Manual-L11.pdf",
}

HELP_TEXT = f"""
{Fore.YELLOW}Available commands:{Style.RESET_ALL}
  {Fore.CYAN}/help{Style.RESET_ALL}              Show this message
  {Fore.CYAN}/manuals{Style.RESET_ALL}           List loaded manuals and chunk counts
  {Fore.CYAN}/filter maytag{Style.RESET_ALL}     Restrict answers to the Maytag manual
  {Fore.CYAN}/filter midea{Style.RESET_ALL}      Restrict answers to the Midea manual
  {Fore.CYAN}/filter off{Style.RESET_ALL}        Remove manual filter (search all)
  {Fore.CYAN}/clear{Style.RESET_ALL}             Clear conversation history
  {Fore.CYAN}/last{Style.RESET_ALL}              Reprint the last answer and sources
  {Fore.CYAN}quit{Style.RESET_ALL} / {Fore.CYAN}exit{Style.RESET_ALL}        Close the assistant
"""


def _print_sources(sources: list[dict]) -> None:
    unique = {(s["source"], s["page"]) for s in sources}
    refs = sorted(unique, key=lambda x: (x[0], x[1]))
    print(Fore.YELLOW + "\nSources:")
    for source, page in refs:
        print(Fore.YELLOW + f"  • {source}, page {page}")


def _print_manuals() -> None:
    stats = get_collection_stats()
    print(Fore.YELLOW + f"\nLoaded manuals ({len(stats)}):")
    for source, count in sorted(stats.items()):
        print(Fore.YELLOW + f"  • {source}  -  {count} chunks")


def run() -> None:
    history = []
    filter_source: str | None = None
    active_filter_label: str | None = None
    last_result: dict | None = None

    while True:
        try:
            label = f" [{active_filter_label}]" if active_filter_label else ""
            user_input = input(Fore.CYAN + f"\nMechanic{label}: " + Style.RESET_ALL).strip()
        except (EOFError, KeyboardInterrupt):
            print(Fore.GREEN + "\nGoodbye!")
            break

        if not user_input:
            continue

        # --- quit ---
        if user_input.lower() in {"quit", "exit"}:
            print(Fore.GREEN + "\nGoodbye!")
            break

        # --- slash commands ---
        if user_input.startswith("/"):
            parts = user_input.split()
            cmd = parts[0].lower()

            if cmd == "/help":
                print(HELP_TEXT)

            elif cmd == "/manuals":
                _print_manuals()

            elif cmd == "/filter":
                if len(parts) < 2:
                    print(Fore.YELLOW + "Usage: /filter maytag | /filter midea | /filter off")
                else:
                    arg = parts[1].lower()
                    if arg == "off":
                        filter_source = None
                        active_filter_label = None
                        print(Fore.GREEN + "Filter cleared - searching all manuals.")
                    elif arg in MANUAL_ALIASES:
                        filter_source = MANUAL_ALIASES[arg]
                        active_filter_label = arg
                        print(Fore.GREEN + f"Filter set to: {filter_source}")
                    else:
                        print(Fore.YELLOW + f"Unknown filter '{arg}'. Use: maytag, midea, or off.")

            elif cmd == "/clear":
                history = []
                print(Fore.GREEN + "Conversation history cleared.")

            elif cmd == "/last":
                if last_result is None:
                    print(Fore.YELLOW + "No previous answer to display.")
                else:
                    print()
                    print(Style.BRIGHT + "Assistant: " + Style.RESET_ALL + last_result["answer"])
                    _print_sources(last_result["sources"])

            else:
                print(Fore.YELLOW + f"Unknown command '{cmd}'. Type /help for available commands.")

            continue

        # --- query ---
        print(Fore.WHITE + "\nSearching documentation...")

        sources, best_distance, stream = query_stream(
            user_input,
            history=history if history else None,
            filter_source=filter_source,
        )

        print()

        if best_distance > CONFIDENCE_THRESHOLD:
            print(Fore.YELLOW + "!  Note: Limited relevant documentation found - answer may be incomplete.\n")

        print(Style.BRIGHT + "Assistant: " + Style.RESET_ALL, end="", flush=True)

        full_answer = ""
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                print(delta, end="", flush=True)
                full_answer += delta
        print()

        _print_sources(sources)

        log_query(
            query=user_input,
            answer=full_answer,
            sources=sources,
            best_distance=best_distance,
        )

        last_result = {"answer": full_answer, "sources": sources}

        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": full_answer})
        if len(history) > HISTORY_WINDOW * 2:
            history = history[-(HISTORY_WINDOW * 2):]