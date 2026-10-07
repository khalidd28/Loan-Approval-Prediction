import os
import json
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import SimpleImputer

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


# -----------------------------
# Paths
# -----------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.dirname(BASE_DIR)

DATASET_PATH = os.path.join(
    PROJECT_DIR,
    "dataset",
    "loan_data.csv"
)

MODEL_DIR = os.path.dirname(os.path.abspath(__file__))

# -----------------------------
# Load Dataset
# -----------------------------

df = pd.read_csv(DATASET_PATH)

print("Dataset loaded successfully")
print("Dataset shape:", df.shape)


# Remove rows without target
df = df.dropna(subset=["Loan_Status"])


# Convert target
df["Loan_Status"] = df["Loan_Status"].map({
    "Y": 1,
    "N": 0
})


# Remove Loan ID
if "Loan_ID" in df.columns:
    df = df.drop("Loan_ID", axis=1)


# -----------------------------
# Encode categorical columns
# -----------------------------

label_encoders = {}

categorical_columns = df.select_dtypes(
    include=["object"]
).columns


for column in categorical_columns:

    encoder = LabelEncoder()

    df[column] = encoder.fit_transform(
        df[column].astype(str)
    )

    label_encoders[column] = encoder


# -----------------------------
# Separate features and target
# -----------------------------

X = df.drop("Loan_Status", axis=1)
y = df["Loan_Status"]


# -----------------------------
# Handle missing values
# -----------------------------

imputer = SimpleImputer(
    strategy="most_frequent"
)

X = pd.DataFrame(
    imputer.fit_transform(X),
    columns=X.columns
)


# -----------------------------
# Train/Test Split
# -----------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


# -----------------------------
# Models
# -----------------------------

models = {

    "Logistic Regression":
        LogisticRegression(max_iter=1000),

    "Decision Tree":
        DecisionTreeClassifier(
            random_state=42
        ),

    "Random Forest":
        RandomForestClassifier(
            n_estimators=100,
            random_state=42
        )
}


# -----------------------------
# Train and Compare
# -----------------------------

results = {}

best_model = None
best_model_name = None
best_accuracy = 0


for name, model in models.items():

    print("\nTraining:", name)

    model.fit(
        X_train,
        y_train
    )

    predictions = model.predict(X_test)

    accuracy = accuracy_score(
        y_test,
        predictions
    )

    precision = precision_score(
        y_test,
        predictions,
        zero_division=0
    )

    recall = recall_score(
        y_test,
        predictions,
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        predictions,
        zero_division=0
    )


    results[name] = {

        "accuracy": round(
            accuracy * 100,
            2
        ),

        "precision": round(
            precision * 100,
            2
        ),

        "recall": round(
            recall * 100,
            2
        ),

        "f1_score": round(
            f1 * 100,
            2
        )
    }


    print(
        "Accuracy:",
        round(accuracy * 100, 2),
        "%"
    )

    print(
        "Precision:",
        round(precision * 100, 2),
        "%"
    )

    print(
        "Recall:",
        round(recall * 100, 2),
        "%"
    )

    print(
        "F1 Score:",
        round(f1 * 100, 2),
        "%"
    )


    # Find best model

    if accuracy > best_accuracy:

        best_accuracy = accuracy

        best_model = model

        best_model_name = name


# -----------------------------
# Save Best Model
# -----------------------------

def fix_imputer(obj):

    if hasattr(obj, "steps"):
        for _, step in obj.steps:
            fix_imputer(step)

    if hasattr(obj, "transformers_"):
        for _, transformer, _ in obj.transformers_:
            fix_imputer(transformer)

    if isinstance(obj, SimpleImputer):

        if not hasattr(obj, "_fill_dtype"):
            obj._fill_dtype = obj.statistics_.dtype

        if not hasattr(obj, "_fit_dtype"):
            obj._fit_dtype = obj.statistics_.dtype


# Fix compatibility
fix_imputer(best_model)
fix_imputer(imputer)


joblib.dump(
    best_model,
    os.path.join(
        MODEL_DIR,
        "loan_model.pkl"
    )
)

joblib.dump(
    list(X.columns),
    os.path.join(
        MODEL_DIR,
        "model_columns.pkl"
    )
)

joblib.dump(
    label_encoders,
    os.path.join(
        MODEL_DIR,
        "label_encoders.pkl"
    )
)

joblib.dump(
    imputer,
    os.path.join(
        MODEL_DIR,
        "imputer.pkl"
    )
)
# -----------------------------
# Save Model Comparison
# -----------------------------

comparison_data = {

    "best_model": best_model_name,

    "models": results
}


with open(
    os.path.join(
        MODEL_DIR,
        "model_metrics.json"
    ),
    "w"
) as file:

    json.dump(
        comparison_data,
        file,
        indent=4
    )


# -----------------------------
# Final Output
# -----------------------------

print("\n==============================")
print("MODEL COMPARISON")
print("==============================")

for name, metrics in results.items():

    print(
        f"{name}: "
        f"{metrics['accuracy']}% accuracy"
    )


print("\nBest Model:", best_model_name)

print(
    "Model saved successfully!"
)