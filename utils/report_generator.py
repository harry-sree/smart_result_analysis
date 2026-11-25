import os
import pandas as pd


def create_class_report(df, output_folder):

    report = (
        df.groupby("class")
        .agg(
            total_students=("student_id", "nunique"),
            average_marks=("final_score", "mean"),
            pass_count=(
                "result",
                lambda x: (x == "Pass").sum()
            ),
            fail_count=(
                "result",
                lambda x: (x == "Fail").sum()
            )
        )
        .reset_index()
    )

    report["pass_percentage"] = (
        report["pass_count"]
        / (
            report["pass_count"]
            + report["fail_count"]
        )
        * 100
    )

    report["average_marks"] = report[
        "average_marks"
    ].round(2)

    report["pass_percentage"] = report[
        "pass_percentage"
    ].round(2)

    path = os.path.join(
        output_folder,
        "class_performance_report.csv"
    )

    report.to_csv(
        path,
        index=False
    )

    return path


def create_subject_report(
    df,
    output_folder
):

    report = (
        df.groupby("subject")
        .agg(
            average_marks=("final_score", "mean"),
            highest_marks=("final_score", "max"),
            lowest_marks=("final_score", "min"),
            pass_count=(
                "result",
                lambda x: (x == "Pass").sum()
            ),
            fail_count=(
                "result",
                lambda x: (x == "Fail").sum()
            )
        )
        .reset_index()
    )

    report["pass_percentage"] = (
        report["pass_count"]
        /
        (
            report["pass_count"]
            + report["fail_count"]
        )
        * 100
    ).round(2)

    path = os.path.join(
        output_folder,
        "subject_performance_report.csv"
    )

    report.to_csv(
        path,
        index=False
    )

    return path


def create_student_report(
    df,
    output_folder
):

    path = os.path.join(
        output_folder,
        "student_performance_report.csv"
    )

    df.to_csv(
        path,
        index=False
    )

    return path