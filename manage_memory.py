from database import init_database, save_long_term_memory, save_user_preference


def main() -> None:
    init_database()

    print("Choose what you want to save:")
    print("1. Long-term memory")
    print("2. User preference")
    choice = input("Enter 1 or 2: ").strip()

    if choice == "1":
        category = input("Memory category (relationship, trading, personal, goals): ").strip()
        content = input("Memory content: ").strip()
        importance_text = input("Importance from 1 to 5 [default 3]: ").strip()
        importance = int(importance_text) if importance_text else 3
        save_long_term_memory(category, content, importance=importance, source="manual")
        print("Long-term memory saved.")
        return

    if choice == "2":
        preference_key = input("Preference key: ").strip()
        preference_value = input("Preference value: ").strip()
        save_user_preference(preference_key, preference_value)
        print("User preference saved.")
        return

    print("No changes made.")


if __name__ == "__main__":
    main()
