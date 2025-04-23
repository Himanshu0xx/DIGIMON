from flask import Flask, request, jsonify, session
from flask_cors import CORS
import os
import sqlite3
from datetime import datetime
import re
import joblib
import calendar
from dateutil.parser import parse
import traceback # For detailed error logging

# --- Load Model, Vectorizer, Connect DB (Keep the same) ---
# Make sure these paths are correct for your environment
try:
    model = joblib.load('/home/kali/AI_Project/chat_botcode/vectorized_set/intent_model_v3.pkl')
    vectorizer = joblib.load('/home/kali/AI_Project/chat_botcode/vectorized_set/tfidf_vectorizer_v3.pkl')
    print("Model and vectorizer loaded successfully.")
except FileNotFoundError as e:
    print(f"Error loading model/vectorizer: {e}")
    # Depending on your setup, you might want to exit or handle this more gracefully
    # For now, we'll re-raise the exception to make the issue clear on startup.
    raise e

db_path = '/home/kali/AI_Project/chat_botcode/Database/fund_manager.db'
try:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cursor = conn.cursor()
    print(f"Connected to database: {db_path}")
except sqlite3.Error as e:
    print(f"Database connection error: {e}")
    # Similar to model loading, re-raise for clarity on startup issues.
    raise e

# --- Flask App Setup (Keep the same) ---
app = Flask(__name__)
# Consider using a more secure way to manage secret key in production
app.secret_key = os.urandom(24)
CORS(app)

# --- Helper Functions ---

def predict_intent(text):
    """Predicts the intent of the user input text."""
    try:
        # Ensure text is a string and handle potential None or empty input
        if not text:
            print("Warning: Received empty or None text for intent prediction.")
            return "unknown"
        X = vectorizer.transform([text])
        intent = model.predict(X)[0]
        print(f"Predicted Intent: {intent} for Input: '{text}'")
        return intent
    except Exception as e:
        print(f"Error during intent prediction for input '{text}': {e}")
        traceback.print_exc() # Print traceback for prediction errors
        return "unknown"

# --- Extraction Helpers ---

def extract_amount(text):
    """Extracts the first numerical amount from the text."""
    if not text: return None # Handle empty input
    match = re.search(r'\b\d+(\.\d{1,2})?\b', text)
    # Safely convert to float, return None if no match
    amount = float(match.group()) if match else None
    print(f"Extracted Amount: {amount} from Input: '{text}'")
    return amount

# --- (Keep the improved extract_category from the previous version) ---
def extract_category(text):
    """Extracts the expense category based on keywords using word boundaries."""
    if not text: return 'others' # Handle empty input
    text = text.lower()
    keyword_map = {
         'food': [
            'food', 'eat', 'snack', 'lunch', 'dinner', 'breakfast', 'cafe', 'restaurant', 'coffee', 'pizza', 'burger', 'meal', 'thali'
        ],
        'stationery': [
            'stationery', 'pen', 'pencil', 'eraser', 'notebook', 'book', 'copy', 'paper', 'files', 'markers', 'highlighter'
        ],
        'outing': [
            'outing', 'movie', 'cinema', 'trip', 'vacation', 'picnic', 'tour', 'hangout', 'resort', 'travel' # Note: 'travel' also here
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
            'entertainment', 'netflix', 'subscription', 'spotify', 'games', 'game', 'movie', 'fun', 'play', 'music', 'youtube' # Note: 'movie' also here
        ],
        'others': []
    }
    for category, keywords in keyword_map.items():
        for keyword in keywords:
            # Use word boundaries to avoid partial matches (e.g., 'rest' in 'restaurant')
            # Add a check to ensure keyword is not empty before using in regex
            if keyword and re.search(r'\b' + re.escape(keyword) + r'\b', text):
                print(f"Extracted Category: {category} based on keyword '{keyword}' from Input: '{text}'")
                return category
    print(f"Extracted Category: others (default) for Input: '{text}'")
    return 'others'

# --- Updated extract_date ---
def extract_date(text):
    """Extracts a date from the text, trying specific formats first, then dateutil."""
    if not text:
        now = datetime.now()
        print("Received empty or None text for date extraction. Defaulting to today.")
        return now.strftime('%Y-%m-%d'), now.month, now.year

    # Try specific regex first for formats like YYYY-MM-DD, YYYY-M-D etc.
    # This regex handles YYYY-MM-DD, YYYY-M-D, YYYY/MM/DD, YYYY/M/D
    match = re.search(r'\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b', text)
    try:
        if match:
            year, month, day = map(int, match.groups())
            parsed_date = datetime(year, month, day)
            print(f"Extracted Date (Regex): {parsed_date.strftime('%Y-%m-%d')} from Input: '{text}'")
            return parsed_date.strftime('%Y-%m-%d'), parsed_date.month, parsed_date.year
        else:
            # Fallback to dateutil.parser for more complex phrases
            # Use fuzzy=True carefully, might misinterpret numbers. dayfirst=True is region-dependent.
            # Set default to now() to handle cases where no date is found
            # Add a check for empty string before parsing
            if text.strip():
                parsed_date = parse(text, fuzzy=True, default=datetime.now(), dayfirst=True)
                # Check if parse actually found a date different from default within the string
                # This is tricky, as fuzzy might find *something*. A better check might be needed.
                # Heuristic: If the parsed date is today AND 'today' isn't in the text, it might be a default fallback
                is_default_date = (parsed_date.date() == datetime.now().date() and
                                   'today' not in text.lower() and
                                   not re.search(r'\b\d{1,2}[-/]\d{1,2}\b', text) and # No obvious partial date
                                   not re.search(r'\b(yesterday|tomorrow)\b', text.lower())) # No relative terms

                if is_default_date and match is None: # Double check it wasn't the regex match case
                     now = datetime.now()
                     print(f"Date Parsing (dateutil) likely defaulted for Input: '{text}'. Using today.")
                     return now.strftime('%Y-%m-%d'), now.month, now.year
                else:
                    print(f"Extracted Date (dateutil): {parsed_date.strftime('%Y-%m-%d')} from Input: '{text}'")
                    return parsed_date.strftime('%Y-%m-%d'), parsed_date.month, parsed_date.year
            else:
                 now = datetime.now()
                 print("Input text is empty after stripping for dateutil parsing. Defaulting to today.")
                 return now.strftime('%Y-%m-%d'), now.month, now.year

    except (ValueError, OverflowError, TypeError) as e:
        # If any parsing fails, default to now
        now = datetime.now()
        print(f"Date Parsing Failed for Input: '{text}'. Error: {e}. Defaulting to today.")
        return now.strftime('%Y-%m-%d'), now.month, now.year

# --- (Keep extract_month as is) ---
def extract_month(text):
    """Extracts a month number (1-12) from text."""
    if not text: return None # Handle empty input
    month_map = {name.lower(): num for num, name in enumerate(calendar.month_name) if num}
    month_abbr_map = {name.lower(): num for num, name in enumerate(calendar.month_abbr) if num}
    month_map.update(month_abbr_map) # Add abbreviations

    for word in text.lower().split():
        if word in month_map:
            month_num = month_map[word]
            print(f"Extracted Month: {month_num} based on word '{word}' from Input: '{text}'") # Added logging
            return month_num
    print(f"Could not extract month from Input: '{text}'") # Added logging
    return None


# --- Intent Handlers (Keep implementations the same as previous version) ---
# Ensure they use the updated extract_date where applicable
def handle_greet():
    """Handles greeting intents."""
    return "👋 Hello! How can I help you with your finances?"

def handle_add_expense(text):
    amount = extract_amount(text)
    category = extract_category(text)
    date_str, month, year = extract_date(text) # Uses updated function

    if not amount:
        return "❌ Sorry, I couldn't find the amount. Please specify the amount spent (e.g., 'spent 50 on food')."
    # Refine the condition for asking clarification for 'others'
    # Only ask if the extracted category is 'others' AND the word 'others' wasn't explicitly in the input
    if category == 'others' and not re.search(r'\bothers\b', text.lower() if text else ''):
        # If default category is 'others' but 'others' wasn't mentioned, ask for clarification
         return f"✅ {amount} added on {date_str}. Which category should I assign this to? (e.g., food, transport, etc.)"

    try:
        cursor.execute("INSERT INTO expenses (date, category, month, year, amount) VALUES (?, ?, ?, ?, ?)",
                       (date_str, category, month, year, amount))
        conn.commit()
        return f"✅ {amount} added to {category} on {date_str}"
    except sqlite3.Error as e:
        print(f"Database error in handle_add_expense: {e}")
        return "❌ Database error while adding expense."
    except Exception as e:
        print(f"Unexpected error in handle_add_expense: {e}")
        traceback.print_exc()
        return "❌ An unexpected error occurred while adding expense."


def handle_add_income(text):
    amount = extract_amount(text)
    date_str, month, year = extract_date(text) # Uses updated function

    if not amount:
        return "❌ Please provide a valid amount for the income."

    try:
        cursor.execute("INSERT INTO income (date, month, year, amount) VALUES (?, ?, ?, ?)",
                       (date_str, month, year, amount))
        conn.commit()
        return f"✅ Income of {amount} added on {date_str}"
    except sqlite3.Error as e:
        print(f"Database error in handle_add_income: {e}")
        return "❌ Database error while adding income."
    except Exception as e:
        print(f"Unexpected error in handle_add_income: {e}")
        traceback.print_exc()
        return "❌ An unexpected error occurred while adding income."

def handle_check_balance():
    try:
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM income") # Use COALESCE to handle NULL sum
        total_income = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses") # Use COALESCE
        total_expense = cursor.fetchone()[0]
        balance = total_income - total_expense
        return f"💰 Total Income: {total_income:.2f}\n💸 Total Expenses: {total_expense:.2f}\n🧾 Balance: {balance:.2f}" # Format balance
    except sqlite3.Error as e:
        print(f"Database error in handle_check_balance: {e}")
        return "❌ Database error while checking balance."
    except Exception as e:
        print(f"Unexpected error in handle_check_balance: {e}")
        traceback.print_exc()
        return "❌ An unexpected error occurred while checking balance."


def handle_show_by_category(text):
    if not text: return "❓ Which category would you like to see?" # Handle empty input
    category = extract_category(text)
    # Improved logic: If category defaults to 'others' but no category keyword was found, ask.
    if category == 'others':
         found_specific_category = False
         temp_text = text.lower() if text else ''
         # Access keyword map - ensure it's accessible if defined outside
         # A more robust way would be to pass keyword_map or make extract_category a class method
         # For now, rely on __globals__ but be aware of its limitations
         keyword_map_local = extract_category.__globals__.get('keyword_map', {})
         for cat, keywords in keyword_map_local.items():
             if cat == 'others': continue
             for kw in keywords:
                 # Add check for empty keyword
                 if kw and re.search(r'\b' + re.escape(kw) + r'\b', temp_text):
                     found_specific_category = True
                     break
             if found_specific_category: break
         # If category is 'others' AND no specific keyword was found in the original text
         if not found_specific_category and not re.search(r'\bothers\b', temp_text):
             return "❓ Which category would you like to see? (e.g., show expenses for food, travel, groceries)"

    try:
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE category = ?", (category,))
        total = cursor.fetchone()[0]
        if total > 0:
            return f"📊 Total spent on {category}: {total:.2f}"
        else:
             # Check if the category exists even if the total is 0
             cursor.execute("SELECT 1 FROM expenses WHERE category = ? LIMIT 1", (category,))
             if cursor.fetchone():
                 return f"📊 Total spent on {category}: 0.00"
             else:
                 # Category might be invalid or just have no entries yet
                 # Check if it was explicitly asked for vs. inferred
                 # Use the original text for this check
                 if re.search(r'\b' + re.escape(category) + r'\b', text.lower() if text else '') or category != 'others':
                    return f"📊 No expenses recorded for the category '{category}' yet."
                 else: # If 'others' was inferred and nothing found, stick to asking which category
                    return "❓ Which category would you like to see? (e.g., show expenses for food, travel, groceries)"

    except sqlite3.Error as e:
        print(f"Database error in handle_show_by_category: {e}")
        return f"❌ Database error while showing category {category}."
    except Exception as e:
        print(f"Unexpected error in handle_show_by_category: {e}")
        traceback.print_exc()
        return f"❌ An unexpected error occurred while showing category {category}."


def handle_show_by_month(text):
    if not text: return "❌ Could not determine the month. Please specify a month name." # Handle empty input
    month_num = extract_month(text)
    if not month_num:
        return "❌ Could not determine the month. Please specify a month name (e.g., 'summary for April')."
    try:
        month_name = calendar.month_name[month_num]
        # Check for year - TBD: Enhance extract_month or add extract_year
        # For now, assumes current year or year mentioned alongside month if any
        current_year = datetime.now().year
        # Simple check if a year is mentioned nearby
        year_match = re.search(r'\b(20\d{2})\b', text)
        target_year = int(year_match.group(1)) if year_match else current_year

        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE month = ? AND year = ?", (month_num, target_year))
        total_expense = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM income WHERE month = ? AND year = ?", (month_num, target_year))
        total_income = cursor.fetchone()[0]

        if total_expense == 0 and total_income == 0:
            return f"📅 No records found for {month_name} {target_year}."
        else:
            return f"📅 {month_name} {target_year} Summary:\n💸 Expenses: {total_expense:.2f}\n💰 Income: {total_income:.2f}\n🧾 Balance: {total_income - total_expense:.2f}"
    except sqlite3.Error as e:
        print(f"Database error in handle_show_by_month: {e}")
        return f"❌ Database error while showing month {month_num}."
    except IndexError:
         return "❌ Invalid month number extracted."
    except Exception as e:
        print(f"Unexpected error in handle_show_by_month: {e}")
        traceback.print_exc()
        return f"❌ An unexpected error occurred while showing month."


def handle_show_by_date(text):
    if not text:
         now = datetime.now()
         date_str = now.strftime('%Y-%m-%d')
         print("Received empty or None text for show_by_date. Using today.")
    else:
        date_str, _, _ = extract_date(text) # Uses updated function

    try:
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE date = ?", (date_str,))
        expense = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM income WHERE date = ?", (date_str,))
        income = cursor.fetchone()[0]

        if expense == 0 and income == 0:
             # Check if the date is today, provide a slightly different message
             if date_str == datetime.now().strftime('%Y-%m-%d'):
                 return f"📅 No income or expenses recorded for today ({date_str}) yet."
             else:
                 return f"📅 No records found for {date_str}."
        else:
            return f"📅 {date_str} Summary:\n💸 Expenses: {expense:.2f}\n💰 Income: {income:.2f}\n🧾 Balance: {income - expense:.2f}"
    except sqlite3.Error as e:
        print(f"Database error in handle_show_by_date: {e}")
        return f"❌ Database error while showing date {date_str}."
    except Exception as e:
        print(f"Unexpected error in handle_show_by_date: {e}")
        traceback.print_exc()
        return f"❌ An unexpected error occurred while showing date."


def handle_goodbye():
    """Handles goodbye intents."""
    return "👋 Goodbye! Feel free to reach out anytime."

def handle_thank_you():
    """Handles thank you intents."""
    return "😊 You're welcome! Let me know if you need anything else."
# --- End of Intent Handlers ---


# --- Main Chatbot Route ---
@app.route("/chat", methods=["POST"])
def chat():
    """Main endpoint to handle user chat messages."""
    try:
        # Safely get the message, defaulting to None if not present
        user_input = request.json.get("message")
        print(f"Received message: {user_input}") # Added logging

        # Check if user_input is None or empty after stripping
        if not user_input or not user_input.strip():
             print("Received empty or whitespace-only message.")
             return jsonify({"response": "Received empty message. How can I help?"}), 400

        # --- Special check for -1 ---
        if user_input.strip() == "-1":
            print("Handling special request for input '-1'") # Added logging
            response_data = {
                "text": "You cannot hack this Prachi!!!",
                "image_path": "/home/kali/AI_Project/frontend/images/connor.jpeg" # Ensure this path is accessible by the frontend
            }
            print("Prepared special response data for -1.") # Added logging
            # Use a distinct key for the frontend to identify this special response
            return jsonify({"special_response": response_data})
        # --- End of -1 check ---

        # --- Rule-based Intent Override ---
        # Check for patterns indicating show_by_date intent
        # More robust date pattern matching YYYY-MM-DD, YYYY/MM/DD, potentially DD-MM-YYYY etc.
        # Example: look for 'on DD/MM/YYYY', 'for YYYY-MM-DD', 'summary YYYY/MM/DD'
        # This regex is an example, might need refinement based on common user inputs
        date_pattern = r'\b(on|for|summary)\s+(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2})\b'
        # Check for month patterns -> show_by_month
        # Example: 'summary for april', 'show june expenses', 'income in 2024 july'
        month_pattern = r'\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\b'
        year_pattern = r'\b(20\d{2})\b' # Matches years like 2023, 2024

        # Determine intent: Rules first, then model prediction
        intent = "unknown" # Default intent

        # Rule for show_by_date
        if re.search(date_pattern, user_input.lower()) and \
           any(kw in user_input.lower() for kw in ['show', 'what', 'how much', 'summary', 'spent', 'income', 'expenses', 'records', 'details']):
             print("Rule Applied: Intent set to show_by_date based on date pattern.")
             intent = 'show_by_date'
        # Rule for show_by_month (avoid triggering if a specific day was also mentioned)
        elif re.search(month_pattern, user_input.lower()) and not re.search(date_pattern, user_input.lower()) and \
             any(kw in user_input.lower() for kw in ['show', 'what', 'how much', 'summary', 'spent', 'income', 'expenses', 'records', 'details', 'month', 'monthly']):
             # Check if year is also mentioned to potentially refine query later
             year_mentioned = re.search(year_pattern, user_input.lower()) is not None
             print(f"Rule Applied: Intent set to show_by_month (Year Mentioned: {year_mentioned}).")
             intent = 'show_by_month'
        # Fallback to model prediction if no rules match strongly
        else:
            print("No specific rule matched, using model prediction.")
            intent = predict_intent(user_input)
        # --- End of Rule-based Override ---


        response_text = ""

        # --- Updated Intent Mapping ---
        intent_handlers = {
            'add_expense': handle_add_expense,
            'add_income': handle_add_income,
            'check_balance': handle_check_balance,
            'show_by_category': handle_show_by_category,
            'show_by_month': handle_show_by_month,
            'show_by_date': handle_show_by_date,
            'greeting': handle_greet, # Ensure model predicts 'greeting'
            'goodbye': handle_goodbye,
            'thank_you': handle_thank_you,
            # Add mappings for any other intents your model predicts
        }

        handler = intent_handlers.get(intent)

        if handler:
            # Pass user_input to handlers that need it
            if intent in ['add_expense', 'add_income', 'show_by_category', 'show_by_month', 'show_by_date']:
                response_text = handler(user_input)
            else: # check_balance, greeting, goodbye, thank_you don't need user_input passed
                response_text = handler()
        else:
            # Handle unknown or unmapped intents
            print(f"Warning: Unhandled or Unknown intent '{intent}' for input: '{user_input}'")
            # Provide more helpful fallback
            if user_input and "how are you" in user_input.lower():
                response_text = "I'm just a bot, but I'm ready to help with your finances!"
            elif user_input and "help" in user_input.lower():
                response_text = "I can help you track income and expenses, check balances, and show summaries by date, month, or category. Try saying 'add 50 expense for food' or 'show my balance'."
            else:
                response_text = "🤖 Sorry, I couldn't quite understand that. Could you please rephrase? You can ask me to add income/expenses, check balance, or show summaries."

        print(f"Sending standard response: {response_text}") # Added logging
        # Always return the standard response format unless it's the special -1 case
        return jsonify({"response": response_text})

    except Exception as e:
        print(f"Error in /chat endpoint: {e}") # Added logging
        traceback.print_exc() # Print detailed traceback for debugging
        return jsonify({"error": "An internal server error occurred. Please try again."}), 500

# --- Run App ---
if __name__ == "__main__":
    # Set debug=False for production environments
    # Use host='0.0.0.0' to make the server accessible on your network
    # Ensure the port is open and accessible from your frontend
    app.run(debug=True, host='0.0.0.0', port=5000)