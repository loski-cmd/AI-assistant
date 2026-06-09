from database import init_database


def main() -> None:
    init_database()
    print("User profile table is ready.")


if __name__ == "__main__":
    main()
