# 💸 FundMate

**AI-Powered Personalized Funds Manager for Students**

---

## 📌 Overview

**FundMate** is a smart financial assistant made just for students. It helps them manage their money easily through a chatbot that understands natural language. Whether it's logging expenses, checking spending, or setting savings goals, FundMate makes it all super simple.

---

## 🎯 Problem We Solved

Many students struggle to manage their money. They often:
- Have irregular income (like scholarships, pocket money)
- Use their phones more than notebooks or Excel sheets
- Need guidance but don’t get it from traditional tools

**FundMate** was created to give students:
- An easy-to-use, 24/7 assistant
- A fun interface for budgeting
- Personalized insights and smart savings tips

---

## 🧠 How It Works

Here’s how the app works behind the scenes:

1. **Student types in a message** like:
   > "Add ₹500 from scholarship on 15th April"

2. The app processes the text:
   - Cleans and simplifies it (lowercase, remove extra stuff)
   - Turns the words into numbers using **TF-IDF**
   - Uses **Logistic Regression** to figure out what the student wants (add expense, show summary, etc.)

3. Then, based on what the user said:
   - It saves or reads data from a simple file (CSV)
   - Shows the result using a cool chat interface

---

## 🖥️ User Interface

### 🎮 Chatbot View:
- Looks like a cute game character
- Talks in a speech bubble
- Makes budgeting feel fun and casual

### 🎨 Login Page:
- Has animation and a mascot
- Engaging and playful, not boring!

---

## 🏗️ App Architecture

```txt
User Interface (Streamlit)
│
├── Input Preprocessing
│
├── NLP Model (TF-IDF + Logistic Regression)
│
├── Intent Handler (Decides what to do)
│
└── CSV File (Stores income and expenses)

## 👨‍💻 Team Members  
- RAHUL BANYALA - KU2407U.
- HIMANSHU KUMAR SINGH - KU2407U406.
- TILAK POPAT - KU2407U.
