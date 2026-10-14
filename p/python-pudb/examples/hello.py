"""Minimal script for testing the python-pudb Dappy plugin."""


def greet(name: str) -> str:
    message = f"Hello, {name}!"
    return message


def main() -> None:
    name = "PuDB"
    result = greet(name)
    print(result)


if __name__ == "__main__":
    main()
