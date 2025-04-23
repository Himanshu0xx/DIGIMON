import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import joblib

#  Step 1: Load the dataset
data_path = '/home/kali/AI_Project/chat_botcode/dataset/fundsmanager_augmented_1050_with_heart(1).csv'  # Update if needed
df = pd.read_csv(data_path)

df.dropna(subset=['text', 'intent'], inplace=True)

# Now proceed with text and label extraction
X = df['text']
y = df['intent']

#  Step 3: Vectorize using TF-IDF
vectorizer = TfidfVectorizer()
X_vectorized = vectorizer.fit_transform(X)

#  Step 4: Train Logistic Regression model
model = LogisticRegression()
model.fit(X_vectorized, y)

#  Step 5: Save the model and vectorizer
model_path = '/home/kali/AI_Project/chat_botcode/vectorized_set/intent_model_v3.pkl'
vectorizer_path = '/home/kali/AI_Project/chat_botcode/vectorized_set/tfidf_vectorizer_v3.pkl'

joblib.dump(model, model_path)
joblib.dump(vectorizer, vectorizer_path)

print("✅ Model and vectorizer saved successfully.")