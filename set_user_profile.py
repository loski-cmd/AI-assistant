from database import init_database, save_user_profile


def main() -> None:
    init_database()

    name = input("Enter your name: ")
    mood = input("How are you feeling today?: ")
    trading_goal = input("What's your current trading goal?: ")

    save_user_profile(name, mood, trading_goal)
    print("User profile saved successfully.")


if __name__ == "__main__":
    main()
