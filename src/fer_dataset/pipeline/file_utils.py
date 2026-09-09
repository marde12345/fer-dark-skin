from pathlib import Path


def clear_directory(directory: Path, pattern: str = "*") -> None:
    if not directory.exists():
        return

    for file in directory.glob(pattern):
        if file.is_file():
            file.unlink()