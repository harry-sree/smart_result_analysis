import os
import joblib

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from sklearn.linear_model import (
    LinearRegression,
    Ridge
)

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

from ml.preprocessing import create_preprocessor


REGRESSION_MODELS = {
    "Linear Regression": LinearRegression(),

    "Ridge Regression": Ridge(
        alpha=1.0
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


def train_regression_models(
    df,
    model_folder
):

    os.makedirs(model_folder, exist_ok=True)

    X = df[FEATURES].copy()
    y = df["final_score"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42
    )

    results = {}

    for name, model in REGRESSION_MODELS.items():

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

        pipeline.fit(
            X_train,
            y_train
        )

        predictions = pipeline.predict(
            X_test
        )

        mae = mean_absolute_error(
            y_test,
            predictions
        )

        rmse = mean_squared_error(
            y_test,
            predictions
        ) ** 0.5

        r2 = r2_score(
            y_test,
            predictions
        )

        filename = (
            name.lower()
            .replace(" ", "_")
            + ".joblib"
        )

        path = os.path.join(
            model_folder,
            filename
        )

        joblib.dump(
            pipeline,
            path
        )

        results[name] = {
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "r2": round(r2, 4)
        }

    return results


def load_regression_model(
    model_folder,
    model_name="Ridge Regression"
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