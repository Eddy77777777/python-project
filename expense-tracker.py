import csv
import datetime

FILE_NAME = "expenses.csv"

# Initialize CSV file with headers if it doesn't exist
def init_file():
    try:
        with open(FILE_NAME, "x", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Date", "Category", "Amount", "Note"])
    except FileExistsError:
        pass

# Add new expense
def add_expense():
    date = input("Enter date (YYYY-MM-DD) or press Enter for today: ")
    if not date:
        date = datetime.date.today().isoformat()

    category = input("Enter category (Food, Travel, Shopping, etc.): ")
    amount = float(input("Enter amount: "))
    note = input("Enter a note (optional): ")

    with open(FILE_NAME, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([date, category, amount, note])

    print("✅ Expense added successfully!")

# View all expenses
def view_expenses():
    with open(FILE_NAME, "r") as file:
        reader = csv.reader(file)
        for row in reader:
            print(row)

# Show monthly total
def monthly_summary():
    month = input("Enter month (YYYY-MM): ")
    total = 0

    with open(FILE_NAME, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["Date"].startswith(month):
                total += float(row["Amount"])

    print(f"💰 Total expenses for {month}: {total}")

# Main menu
def main():
    init_file()
    while True:
        print("\n==== Expense Tracker ====")
        print("1. Add Expense")
        print("2. View All Expenses")
        print("3. Monthly Summary")
        print("4. Exit")

        choice = input("Choose an option: ")

        if choice == "1":
            add_expense()
        elif choice == "2":
            view_expenses()
        elif choice == "3":
            monthly_summary()
        elif choice == "4":
            print("👋 Exiting... Have a nice day!")
            break
        else:
            print("❌ Invalid choice, try again.")

if __name__ == "__main__":
    main()
