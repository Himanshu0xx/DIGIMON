import joblib
import sqlite3
import calendar
import re
from datetime import datetime
from dateutil.parser import parse

# Load model and vectorizer
# Make sure the paths to your model and vectorizer files are correct
try:
    model = joblib.load("chat_botcode/vectorized_set/intent_model_v3.pkl")
    vectorizer = joblib.load("chat_botcode/vectorized_set/tfidf_vectorizer_v3.pkl")
except FileNotFoundError:
    print("Error: Model or vectorizer file not found. Please check the paths.")
    # You might want to exit or handle this error more gracefully
    exit()


# Connect to DB
conn = sqlite3.connect("fund_manager.db")
cursor = conn.cursor()

# Create tables if they don't exist
cursor.execute('''CREATE TABLE IF NOT EXISTS expenses
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, category TEXT, month INTEGER, year INTEGER, amount REAL)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS income
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, time TEXT, month INTEGER, year INTEGER, amount REAL)''')
conn.commit()


def extract_category(text):
    """
    Extracts a spending category from the input text based on keywords.
    """
    text = text.lower()

    keyword_map = {
        'food': [
            'food', 'eat', 'snack', 'lunch', 'dinner', 'breakfast', 'cafe', 'restaurant', 'coffee', 'pizza', 'burger', 'meal', 'thali'
        ],
        'stationery': [
            'stationery', 'pen', 'pencil', 'eraser', 'notebook', 'book', 'copy', 'paper', 'files', 'markers', 'highlighter'
        ],
        'outing': [
            'outing', 'movie', 'cinema', 'trip', 'vacation', 'picnic', 'tour', 'hangout', 'resort', 'travel'
        ],
        'transport': [
            'transport', 'bus', 'train', 'cab', 'taxi', 'auto', 'ride', 'metro', 'flight', 'fare', 'bike', 'uber', 'ola'
        ],
        'fees': [
            'fees', 'tuition', 'school', 'college', 'exam', 'admission', 'registration', 'course', 'classes', 'coaching'
        ],
        'heart': [
            'heart', 'girlfriend', 'boyfriend', 'partner', 'crush', 'date', 'love', 'darling', 'sweetheart', 'bae', 'him', 'her', 'anniversary', 'valentine'
        ],
        'clothing': [
            'clothes', 'clothing', 'dress', 'shirt', 'tshirt', 'jeans', 'hoodie', 'kurta', 'lehenga', 'suit', 'apparel', 'jacket'
        ],
        'groceries': [
            'grocery', 'groceries', 'vegetables', 'fruits', 'milk', 'bread', 'eggs', 'ration', 'supermarket'
        ],
        'entertainment': [
            'entertainment', 'netflix', 'subscription', 'spotify', 'games', 'game', 'movie', 'fun', 'play', 'music', 'youtube'
        ],
        'others': [] # Keep 'others' at the end as a fallback
    }

    for category, keywords in keyword_map.items():
        # Ensure 'others' is only matched if no other category is found
        if category == 'others':
            continue

        for keyword in keywords:
            # Use regex to match whole words
            if re.search(r'\b' + re.escape(keyword) + r'\b', text):
                return category # Return the first category with a whole word match

    return 'others' # Default if no keywords match


def extract_amount(text):
    """
    Extracts a numerical amount from the input text.
    """
    # Look for numbers, optionally with a decimal point
    match = re.search(r'\b\d+(\.\d{1,2})?\b', text)
    try:
        return float(match.group()) if match else None
    except ValueError:
        return None # Return None if conversion to float fails


def extract_date_info(text):
    """
    Extracts date, month, and year information from text.
    Returns a dictionary with 'date', 'month', 'year' keys.
    Values can be None if not found.
    """
    text = text.lower()
    date_info = {'date': None, 'month': None, 'year': None}
    now = datetime.now()

    # Try to parse a full date first (YYYY-MM-DD, MM/DD/YYYY, etc.)
    try:
        # Use strict=False to allow fuzzy matching but prioritize clear formats
        parsed_date = parse(text, fuzzy=True, dayfirst=False, strict=False)
        date_info['date'] = parsed_date.strftime('%Y-%m-%d')
        date_info['month'] = parsed_date.month
        date_info['year'] = parsed_date.year
        return date_info
    except Exception:
        pass # If parsing as a full date fails, continue

    # If a full date wasn't parsed, try to extract month and year separately
    months = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
    year_match = re.search(r'\b(20\d{2})\b', text) # Look for a 4-digit year starting with 20
    year = int(year_match.group(1)) if year_match else None # Don't default year here, handle in handlers

    for word in text.split():
        # Handle month names
        if word in months:
            date_info['month'] = months[word]
            # If a year was found along with a month, use it
            if year is not None:
                 date_info['year'] = year
            return date_info # Return month (and potentially year) if found

    # If only a year is found
    if year is not None:
         date_info['year'] = year
         return date_info

    # If no specific date, month, or year is mentioned
    return date_info

# -------- Handler Functions -------- #
def handle_add_expense(text):
    amount = extract_amount(text)
    category = extract_category(text)
    date_info = extract_date_info(text)
    date_str = date_info.get('date')
    month = date_info.get('month')
    year = date_info.get('year')

    if not amount:
        return "❌ Sorry, I couldn't find the amount for the expense. Please tell me the amount."

    # If date is missing, ask the user
    if not date_str:
         return "🗓️ I have the amount and category, but I need the date for this expense. Could you please provide it?"

    # If month or year are missing after date parsing (shouldn't happen if date_str exists from parse),
    # or if date was provided in a format that parse couldn't get month/year from (unlikely with fuzzy=True)
    # you might add a fallback here, but with the current extract_date_info it should be okay.
    if month is None or year is None:
         # This case should be rare if date_str is available from successful parsing
         # You could add a log or a more specific error if needed
         return "❗ There was an issue processing the date information. Please try again or provide the date in YYYY-MM-DD format."


    print(f"Attempting to add expense: Amount: {amount}, Category: {category}, Date: {date_str}, Month: {month}, Year: {year}")
    try:
        cursor.execute("INSERT INTO expenses (date, category, month, year, amount) VALUES (?, ?, ?, ?, ?)",
                       (date_str, category, month, year, amount))
        conn.commit()
        return f"✅ {amount} added to {category} on {date_str}"
    except Exception as e:
        conn.rollback() # Rollback in case of error
        return f"❗ An error occurred while adding the expense: {e}"


def handle_add_income(text):
    amount = extract_amount(text)
    date_info = extract_date_info(text)
    date_str = date_info.get('date')
    month = date_info.get('month')
    year = date_info.get('year')
    time_str = datetime.now().strftime('%H:%M:%S') # Capture time regardless of date input

    if not amount:
        return "❌ Please provide a valid amount for the income."

    # If date is missing, ask the user
    if not date_str:
        return "🗓️ I have the income amount, but I need the date. Could you please provide it?"

    if month is None or year is None:
        # This case should be rare if date_str is available from successful parsing
        return "❗ There was an issue processing the date information for income. Please try again or provide the date in YYYY-MM-DD format."


    print(f"Attempting to add income: Amount: {amount}, Date: {date_str}, Month: {month}, Year: {year}, Time: {time_str}")
    try:
        cursor.execute("INSERT INTO income (date, time, month, year, amount) VALUES (?, ?, ?, ?, ?)",
                       (date_str, time_str, month, year, amount))
        conn.commit()
        return f"✅ Income of {amount} added on {date_str}"
    except Exception as e:
        conn.rollback() # Rollback in case of error
        return f"❗ An error occurred while adding the income: {e}"


def handle_check_balance():
    cursor.execute("SELECT SUM(amount) FROM income")
    income = cursor.fetchone()[0] or 0
    cursor.execute("SELECT SUM(amount) FROM expenses")
    expenses = cursor.fetchone()[0] or 0
    return f"💰 Total Income: {income}\n💸 Total Expenses: {expenses}\n🧾 Balance: {income - expenses}"


def handle_show_by_category(text):
    category = extract_category(text)
    # You could add date/month/year filtering here if the user specifies it,
    # by using extract_date_info and modifying the SQL query. For now, it's total.
    cursor.execute("SELECT SUM(amount) FROM expenses WHERE category = ?", (category,))
    total = cursor.fetchone()[0] or 0
    return f"📂 Total spent on {category}: {total}"


def handle_show_by_month(text):
    date_info = extract_date_info(text)
    month_num = date_info.get('month')
    year = date_info.get('year')

    if not month_num:
        return "❌ I can show you expenses and income for a specific month, but I need to know which month you're asking about."

    # If year is not specified, assume current year
    if not year:
        year = datetime.now().year

    print(f"Attempting to show summary for Month: {month_num}, Year: {year}")
    try:
        cursor.execute("SELECT SUM(amount) FROM expenses WHERE month = ? AND year = ?", (month_num, year))
        exp = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(amount) FROM income WHERE month = ? AND year = ?", (month_num, year))
        inc = cursor.fetchone()[0] or 0
        return f"📅 {calendar.month_name[month_num]} {year} Summary:\n💸 Expenses: {exp}\n💰 Income: {inc}\n🧾 Balance: {inc - exp}"
    except Exception as e:
         return f"❗ An error occurred while fetching data for the month: {e}"


def handle_show_by_date(text):
    date_info = extract_date_info(text)
    date_str = date_info.get('date')

    if not date_str:
        return "❌ I can show you expenses and income for a specific date, but I need to know which date you're asking about."

    print(f"Attempting to show summary for Date: {date_str}")
    try:
        cursor.execute("SELECT SUM(amount) FROM expenses WHERE date = ?", (date_str,))
        exp = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(amount) FROM income WHERE date = ?", (date_str,))
        inc = cursor.fetchone()[0] or 0
        return f"📆 {date_str} Summary:\n💸 Expenses: {exp}\n💰 Income: {inc}"
    except Exception as e:
        return f"❗ An error occurred while fetching data for the date: {e}"


def handle_greet():
    return "👋 Hello! How can I help you with your finances?"

def handle_goodbye():
    # Close the database connection before saying goodbye
    conn.close()
    return "👋 Goodbye! Take care."

def handle_thank_you():
    return "🙏 You're welcome!"

# -------- Intent Handler -------- #
def chatbot_response(user_input):
    # Predict intent
    try:
        intent = model.predict(vectorizer.transform([user_input]))[0]
        print(f"\nDetected Intent: {intent}")
        print(f"Raw Input: {user_input}")
    except Exception as e:
        print(f"Error predicting intent: {e}")
        intent = "unknown" # Default to unknown if prediction fails


    if intent == 'add_expense':
        return handle_add_expense(user_input)
    elif intent == 'add_income':
        return handle_add_income(user_input)
    elif intent == 'check_balance':
        return handle_check_balance()
    elif intent == 'show_by_category':
        return handle_show_by_category(user_input)
    elif intent == 'show_by_month':
        return handle_show_by_month(user_input)
    elif intent == 'show_by_date':
        return handle_show_by_date(user_input)
    elif intent == 'greet':
        return handle_greet()
    elif intent == 'goodbye':
        return handle_goodbye()
    elif intent == 'thank_you':
        return handle_thank_you()
    else:
        return "🤖 Sorry, I didn't understand that."

# -------- Run CLI Loop -------- #
def test_chatbot():
    print("💬 Chatbot is ready. Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            print(handle_goodbye()) # Call goodbye handler to close DB
            break
        response = chatbot_response(user_input)
        print("Bot:", response)

# Run chatbot
if __name__ == "__main__":
    test_chatbot()