import re


def extract_pokemon_name(content: str) -> str | None:
    """
    Extract the Pokémon name using the same basic parsing strategy
    as the original script, without any stealth/evasion behavior.
    """

    lines = content.splitlines()
    if not lines:
        return None

    first_line = lines[0].strip()

    # Equivalent to splitting around '<' or ':'
    name = re.split(r"[<:]", first_line, maxsplit=1)[0].strip()

    if not name:
        return None

    # For multi-word names, prefer explicitly supplied names.
    if " " in name:
        best = re.search(
            r"Best name:\s*([^\n]+)",
            content,
            re.IGNORECASE,
        )

        if best:
            return best.group(1).strip()

        shortest = re.search(
            r"Shortest Name:\s*([^\n]+)",
            content,
            re.IGNORECASE,
        )

        if shortest:
            return shortest.group(1).strip()

    return name
