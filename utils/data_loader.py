import os
import pandas as pd


REQUIRED_COLUMNS = [
    "student_id",
    "student_name",
    "gender",
    "class",
    "subject",
    "internal_marks",
    "assignment_marks",
    "attendance",
    "previous_score",
    "final_score",
    "result"
]


def load_dataset(file_path):
    """
    Load CSV or Excel dataset.
    """

    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".csv":
        df = pd.read_csv(file_path)

    elif extension == ".xlsx":
        df = pd.read_excel(file_path)

    else:
        raise ValueError("Only CSV and XLSX files are supported.")

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    validate_columns(df)

    return clean_dataset(df)


def validate_columns(df):
    missing = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Missing required columns: " + ", ".join(missing)
        )


def clean_dataset(df):

    numeric_columns = [
        "internal_marks",
        "assignment_marks",
        "attendance",
        "previous_score",
        "final_score"
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        df[column] = df[column].fillna(
            df[column].median()
        )

    categorical_columns = [
        "student_id",
        "student_name",
        "gender",
        "class",
        "subject",
        "result"
    ]

    for column in categorical_columns:
        df[column] = (
            df[column]
            .fillna("Unknown")
            .astype(str)
            .str.strip()
        )

    # Validate ranges
    df["internal_marks"] = df["internal_marks"].clip(0, 30)
    df["assignment_marks"] = df["assignment_marks"].clip(0, 10)
    df["attendance"] = df["attendance"].clip(0, 100)
    df["previous_score"] = df["previous_score"].clip(0, 100)
    df["final_score"] = df["final_score"].clip(0, 100)

    df["result"] = df["result"].str.title()

    return df