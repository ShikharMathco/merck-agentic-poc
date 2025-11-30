def run_sql_agent():
    print("Running SQL Agent...")
    # Here you would call your SQL agent code
    # For now, just a placeholder
    sql_query = input("Enter your SQL question: ")
    print(f"SQL Agent received query: {sql_query}")


def run_simulator_agent():
    print("Running Simulator Agent...")
    # Here you would call your Simulator agent code
    # Placeholder
    simulation_input = input("Enter simulator input: ")
    print(f"Simulator Agent received input: {simulation_input}")


def main():
    print("Welcome to the Orchestrator!")
    print("Which agent do you want to run?")
    print("1. SQL Agent")
    print("2. Simulator Agent")
    
    choice = input("Enter 1 or 2: ").strip()
    
    if choice == "1":
        run_sql_agent()
    elif choice == "2":
        run_simulator_agent()
    else:
        print("Invalid choice. Please run the program again and choose 1 or 2.")


if __name__ == "__main__":
    main()
