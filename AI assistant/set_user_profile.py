from voice_chat import save_user_profile

name = input("Enter your name: ")
mood = input("How are you feeling today?: ")
trading_goal = input("What’s your current trading goal?: ")

save_user_profile(name, mood, trading_goal)

print("✅ User profile saved!")
