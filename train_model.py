# train_model.py

import pickle
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import pandas as pd
from sklearn.model_selection import train_test_split

# Load and preprocess data
df = pd.read_csv('Placement_Prediction_data.csv')
df.fillna(0, inplace=True)
df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

# Encode categorical fields
le = LabelEncoder()
df['Internship'] = le.fit_transform(df['Internship'])
df['Hackathon'] = le.fit_transform(df['Hackathon'])

X = df.drop(['StudentId', 'PlacementStatus'], axis=1)
y = df['PlacementStatus']

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# ✅ Use Logistic Regression or Random Forest
model = LogisticRegression(max_iter=1000)  # Or use RandomForestClassifier with more depth
# model = RandomForestClassifier(n_estimators=100)

model.fit(X_train, y_train)

# Save placement model
pickle.dump(model, open('model.pkl', 'wb'))

# 🧠 Train salary model similarly
salary_df = pd.read_csv('Salary_prediction_data.csv')
salary_df.fillna(0, inplace=True)
salary_df = salary_df.loc[:, ~salary_df.columns.str.contains('^Unnamed')]

le = LabelEncoder()
salary_df['Internship'] = le.fit_transform(salary_df['Internship'])
salary_df['Hackathon'] = le.fit_transform(salary_df['Hackathon'])
salary_df['PlacementStatus'] = le.fit_transform(salary_df['PlacementStatus'])

X_salary = salary_df.drop(['StudentId', 'salary'], axis=1)
y_salary = salary_df['salary']

X_train_s, X_test_s, y_train_s, y_test_s = train_test_split(X_salary, y_salary, test_size=0.3, random_state=42)

salary_model = RandomForestClassifier(n_estimators=100)
salary_model.fit(X_train_s, y_train_s)

pickle.dump(salary_model, open('model1.pkl', 'wb'))

print("✅ Updated models saved as model.pkl (placement) and model1.pkl (salary)")
