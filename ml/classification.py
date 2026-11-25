import os
import joblib
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)

from ml.preprocessing import create_preprocessor


CLASSIFICATION_MODELS = {
    "Logistic Regression": LogisticRegression(
        max_iter=1000,
        random_state=42
    ),

    "Decision Tree": DecisionTreeClassifier(
        max_depth=6,
        random_state=42
    ),

    "Random Forest": RandomForestClassifier(
        n_estimators=150,
        max_depth=8,
        random_state=42
    )
}


FEATURES = [
    "internal_marks",
    "assignment_marks",
    "attendance",
    "previous_score",
    "gender",
    "class",
    "subject"
]


def train_classification_models(df, model_folder):

    os.makedirs(model_folder, exist_ok=True)

    X = df[FEATURES].copy()

    y = (
        df["result"]
        .str.lower()
        .map({
            "pass": 1,
            "fail": 0
        })
    )

    if y.isna().any():
        raise ValueError(
            "Result column must contain only Pass or Fail."
        )

    if y.nunique() < 2:
        raise ValueError(
            "Dataset must contain both Pass and Fail records."
        )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    results = {}

    for name, model in CLASSIFICATION_MODELS.items():

        pipeline = Pipeline(
            steps=[
                (
                    "preprocessor",
                    create_preprocessor()
                ),
                (
                    "model",
                    model
                )
            ]
        )

        pipeline.fit(X_train, y_train)

        predictions = pipeline.predict(X_test)

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

        matrix = confusion_matrix(
            y_test,
            predictions
        ).tolist()

        filename = (
            name.lower()
            .replace(" ", "_")
            + ".joblib"
        )

        model_path = os.path.join(
            model_folder,
            filename
        )

        joblib.dump(
            pipeline,
            model_path
        )

        results[name] = {
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "confusion_matrix": matrix
        }

    return results


def load_classification_model(
    model_folder,
    model_name="Random Forest"
):

    filename = (
        model_name.lower()
        .replace(" ", "_")
        + ".joblib"
    )

    path = os.path.join(
        model_folder,
        filename
    )

    if not os.path.exists(path):
        return None

    return joblib.load(path)


def predict_student(
    model,
    student_data
):

    data = pd.DataFrame(
        [student_data]
    )

    prediction = model.predict(data)[0]

    if hasattr(model, "predict_proba"):
        probability = model.predict_proba(data)[0]

        # Probability of failure
        failure_probability = float(
            probability[0]
        )

    else:
        failure_probability = 1.0 if prediction == 0 else 0.0

    result = (
        "Pass"
        if prediction == 1
        else "Fail"
    )

    return {
        "prediction": result,
        "failure_probability": failure_probability
    }