import os
import uuid

import pandas as pd

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    session
)

from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from werkzeug.utils import secure_filename


from config import Config

from utils.data_loader import load_dataset
from utils.validators import allowed_file

from utils.report_generator import (
    create_class_report,
    create_subject_report,
    create_student_report
)

from ml.classification import (
    train_classification_models,
    load_classification_model
)

from ml.regression import (
    train_regression_models,
    load_regression_model
)

from ml.evaluation import classification_summary


app = Flask(__name__)
app.config.from_object(Config)


# --------------------------------------------------
# CREATE DIRECTORIES
# --------------------------------------------------

os.makedirs(
    app.config["UPLOAD_FOLDER"],
    exist_ok=True
)

os.makedirs(
    os.path.join(
        app.config["MODEL_FOLDER"],
        "classification"
    ),
    exist_ok=True
)

os.makedirs(
    os.path.join(
        app.config["MODEL_FOLDER"],
        "regression"
    ),
    exist_ok=True
)

os.makedirs(
    app.config["REPORT_FOLDER"],
    exist_ok=True
)


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


class User(UserMixin):

    def __init__(
        self,
        user_id,
        username,
        password,
        role
    ):
        self.id = user_id
        self.username = username
        self.password = password
        self.role = role


users = {
    "admin": User(
        "1",
        "admin",
        generate_password_hash("admin123"),
        "Admin"
    ),

    "faculty": User(
        "2",
        "faculty",
        generate_password_hash("faculty123"),
        "Faculty"
    )
}


@login_manager.user_loader
def load_user(user_id):

    for user in users.values():

        if user.id == user_id:
            return user

    return None


# --------------------------------------------------
# GLOBAL DATA
# --------------------------------------------------

DATA = {
    "df": None,
    "classification": None,
    "regression": None
}


# Load the bundled 500-record example dataset on startup. Users can still upload
# another CSV/XLSX dataset from the existing Upload page at any time.
DEFAULT_DATASET_PATH = os.path.join(
    os.path.dirname(__file__),
    "data",
    "student_results_500.csv"
)
if os.path.exists(DEFAULT_DATASET_PATH):
    DATA["df"] = load_dataset(DEFAULT_DATASET_PATH)


@app.context_processor
def inject_module_chart_data():
    """Provide reusable bar- and pie-chart data to every authenticated module."""
    df = DATA.get("df")
    if df is None or df.empty:
        return {"module_chart_data": None}

    def counts(series):
        result = series.fillna("Unknown").astype(str).value_counts()
        return [{"label": str(k), "value": int(v)} for k, v in result.items()]

    subject_avg = (
        df.groupby("subject", dropna=False)["final_score"].mean().round(2)
        .sort_index()
    )
    class_avg = (
        df.groupby("class", dropna=False)["final_score"].mean().round(2)
        .sort_index()
    )
    result_counts = counts(df["result"]) if "result" in df else []
    gender_counts = counts(df["gender"]) if "gender" in df else []

    # Compare average final scores for male/female (and any other gender labels)
    # within every class. Keep labels data-driven for uploaded datasets.
    class_gender = (
        df.groupby(["class", "gender"], dropna=False)["final_score"]
        .mean().round(2).reset_index()
    )
    class_labels = sorted(df["class"].fillna("Unknown").astype(str).unique().tolist())
    gender_labels = sorted(df["gender"].fillna("Unknown").astype(str).unique().tolist())
    gender_by_class = {
        str(g): [
            float(class_gender.loc[
                (class_gender["class"].astype(str) == c) &
                (class_gender["gender"].astype(str) == g), "final_score"
            ].iloc[0]) if not class_gender.loc[
                (class_gender["class"].astype(str) == c) &
                (class_gender["gender"].astype(str) == g), "final_score"
            ].empty else None
            for c in class_labels
        ] for g in gender_labels
    }

    class_result = df.groupby(["class", "result"], dropna=False).size().reset_index(name="count")
    result_names = sorted(df["result"].fillna("Unknown").astype(str).unique().tolist())
    result_by_class = {
        str(r): [
            int(class_result.loc[
                (class_result["class"].astype(str) == c) &
                (class_result["result"].astype(str) == r), "count"
            ].iloc[0]) if not class_result.loc[
                (class_result["class"].astype(str) == c) &
                (class_result["result"].astype(str) == r), "count"
            ].empty else 0
            for c in class_labels
        ] for r in result_names
    }

    # Convert internal marks (out of 30) and assignment marks (out of 10)
    # to percentages so they can be fairly compared with scores out of 100.
    subject_marks = df.groupby("subject", dropna=False).agg(
        internal=("internal_marks", "mean"),
        assignment=("assignment_marks", "mean"),
        previous=("previous_score", "mean"),
        final=("final_score", "mean")
    ).round(2).sort_index()

    return {"module_chart_data": {
        "subject_labels": [str(x) for x in subject_avg.index],
        "subject_values": [float(x) for x in subject_avg.values],
        "class_labels": [str(x) for x in class_avg.index],
        "class_values": [float(x) for x in class_avg.values],
        "result_labels": [x["label"] for x in result_counts],
        "result_values": [x["value"] for x in result_counts],
        "gender_labels": [x["label"] for x in gender_counts],
        "gender_values": [x["value"] for x in gender_counts],
        "gender_by_class": gender_by_class,
        "result_names": result_names,
        "result_by_class": result_by_class,
        "subject_marks": {
            "labels": [str(x) for x in subject_marks.index],
            "internal_pct": [round(float(x) / 30 * 100, 2) for x in subject_marks["internal"]],
            "assignment_pct": [round(float(x) / 10 * 100, 2) for x in subject_marks["assignment"]],
            "previous_pct": [float(x) for x in subject_marks["previous"]],
            "final_pct": [float(x) for x in subject_marks["final"]]
        }
    }}


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.route(
    "/",
    methods=["GET"]
)
def index():

    if current_user.is_authenticated:
        return redirect(
            url_for("dashboard")
        )

    return redirect(
        url_for("login")
    )


@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        user = users.get(username)

        if user and check_password_hash(
            user.password,
            password
        ):

            login_user(user)

            flash(
                "Login successful.",
                "success"
            )

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid username or password.",
            "danger"
        )

    return render_template(
        "login.html"
    )


@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "You have been logged out.",
        "info"
    )

    return redirect(
        url_for("login")
    )


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():

    df = DATA["df"]

    if df is None:

        return render_template(
            "dashboard.html",
            data_loaded=False
        )

    total_students = (
        df["student_id"]
        .nunique()
    )

    total_subjects = (
        df["subject"]
        .nunique()
    )

    average_score = round(
        df["final_score"].mean(),
        2
    )

    pass_count = (
        df["result"]
        .eq("Pass")
        .sum()
    )

    fail_count = (
        df["result"]
        .eq("Fail")
        .sum()
    )

    total = pass_count + fail_count

    pass_percentage = (
        round(
            pass_count / total * 100,
            2
        )
        if total
        else 0
    )

    fail_percentage = (
        round(
            fail_count / total * 100,
            2
        )
        if total
        else 0
    )

    return render_template(
        "dashboard.html",
        data_loaded=True,
        total_students=total_students,
        total_subjects=total_subjects,
        average_score=average_score,
        pass_count=pass_count,
        fail_count=fail_count,
        pass_percentage=pass_percentage,
        fail_percentage=fail_percentage
    )


# --------------------------------------------------
# UPLOAD
# --------------------------------------------------

@app.route(
    "/upload",
    methods=["GET", "POST"]
)
@login_required
def upload():

    if request.method == "POST":

        file = request.files.get(
            "file"
        )

        if not file or file.filename == "":
            flash(
                "Please select a file.",
                "danger"
            )

            return redirect(
                url_for("upload")
            )

        if not allowed_file(
            file.filename
        ):

            flash(
                "Only CSV and XLSX files are allowed.",
                "danger"
            )

            return redirect(
                url_for("upload")
            )

        filename = secure_filename(
            file.filename
        )

        unique_name = (
            str(uuid.uuid4())
            + "_"
            + filename
        )

        path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            unique_name
        )

        file.save(path)

        try:

            df = load_dataset(path)

            DATA["df"] = df

            # Reset ML results
            DATA["classification"] = None
            DATA["regression"] = None

            session["dataset_loaded"] = True

            flash(
                f"Dataset uploaded successfully. "
                f"{len(df)} records loaded.",
                "success"
            )

            return redirect(
                url_for("dashboard")
            )

        except Exception as error:

            flash(
                str(error),
                "danger"
            )

    return render_template(
        "upload.html"
    )


# --------------------------------------------------
# ANALYSIS
# --------------------------------------------------

@app.route("/analysis")
@login_required
def analysis():

    df = DATA["df"]

    if df is None:

        flash(
            "Please upload a dataset first.",
            "warning"
        )

        return redirect(
            url_for("upload")
        )

    summary = {
        "records": len(df),
        "students": df["student_id"].nunique(),
        "subjects": df["subject"].nunique(),
        "average": round(
            df["final_score"].mean(),
            2
        ),
        "highest": int(
            df["final_score"].max()
        ),
        "lowest": int(
            df["final_score"].min()
        ),
        "attendance": round(
            df["attendance"].mean(),
            2
        )
    }

    subject_data = (
        df.groupby("subject")[
            "final_score"
        ]
        .mean()
        .round(2)
        .to_dict()
    )

    return render_template(
        "analysis.html",
        summary=summary,
        subject_data=subject_data
    )


# --------------------------------------------------
# CLASSIFICATION
# --------------------------------------------------

@app.route(
    "/classification",
    methods=["GET", "POST"]
)
@login_required
def classification():

    df = DATA["df"]

    if df is None:

        flash(
            "Upload a dataset first.",
            "warning"
        )

        return redirect(
            url_for("upload")
        )

    if request.method == "POST":

        try:

            model_folder = os.path.join(
                app.config["MODEL_FOLDER"],
                "classification"
            )

            results = train_classification_models(
                df,
                model_folder
            )

            DATA["classification"] = results

            flash(
                "Classification models trained successfully.",
                "success"
            )

        except Exception as error:

            flash(
                str(error),
                "danger"
            )

    results = DATA["classification"]

    summary = (
        classification_summary(results)
        if results
        else []
    )

    return render_template(
        "classification.html",
        results=summary
    )


# --------------------------------------------------
# REGRESSION
# --------------------------------------------------

@app.route(
    "/regression",
    methods=["GET", "POST"]
)
@login_required
def regression():

    df = DATA["df"]

    if df is None:

        flash(
            "Upload a dataset first.",
            "warning"
        )

        return redirect(
            url_for("upload")
        )

    if request.method == "POST":

        try:

            model_folder = os.path.join(
                app.config["MODEL_FOLDER"],
                "regression"
            )

            results = train_regression_models(
                df,
                model_folder
            )

            DATA["regression"] = results

            flash(
                "Regression models trained successfully.",
                "success"
            )

        except Exception as error:

            flash(
                str(error),
                "danger"
            )

    return render_template(
        "regression.html",
        results=DATA["regression"]
    )


# --------------------------------------------------
# STUDENTS
# --------------------------------------------------

@app.route("/students")
@login_required
def students():

    df = DATA["df"]

    if df is None:

        return redirect(
            url_for("upload")
        )

    students_df = (
        df.groupby(
            [
                "student_id",
                "student_name",
                "gender",
                "class"
            ]
        )
        .agg(
            average_score=(
                "final_score",
                "mean"
            ),
            attendance=(
                "attendance",
                "mean"
            )
        )
        .reset_index()
    )

    students_df["average_score"] = (
        students_df["average_score"]
        .round(2)
    )
    students_df["attendance"] = students_df["attendance"].round(2)

    # Search by student ID, name, gender, or class. An empty search shows all students.
    search_query = request.args.get("q", "").strip()
    if search_query:
        search_mask = pd.Series(False, index=students_df.index)
        for column in ["student_id", "student_name", "gender", "class"]:
            search_mask = search_mask | students_df[column].astype(str).str.contains(
                search_query, case=False, na=False, regex=False
            )
        students_df = students_df.loc[search_mask]

    records = students_df.to_dict(orient="records")

    return render_template(
        "students.html",
        students=records,
        search_query=search_query,
        result_count=len(records)
    )


# --------------------------------------------------
# STUDENT DETAIL
# --------------------------------------------------

@app.route(
    "/students/<student_id>"
)
@login_required
def student_detail(student_id):

    df = DATA["df"]

    if df is None:

        return redirect(
            url_for("upload")
        )

    student_df = df[
        df["student_id"].astype(str) == str(student_id)
    ]

    if student_df.empty:

        flash(
            "Student not found.",
            "danger"
        )

        return redirect(
            url_for("students")
        )

    student = student_df.iloc[0]

    average_score = round(
        student_df["final_score"].mean(),
        2
    )

    subjects = student_df.to_dict(
        orient="records"
    )

    return render_template(
        "student_detail.html",
        student=student,
        subjects=subjects,
        average_score=average_score
    )


# --------------------------------------------------
# SUBJECTS
# --------------------------------------------------

@app.route("/subjects")
@login_required
def subjects():

    df = DATA["df"]

    if df is None:

        return redirect(
            url_for("upload")
        )

    result = (
        df.groupby("subject")
        .agg(
            students=(
                "student_id",
                "nunique"
            ),
            average_marks=(
                "final_score",
                "mean"
            ),
            highest=(
                "final_score",
                "max"
            ),
            lowest=(
                "final_score",
                "min"
            ),
            pass_count=(
                "result",
                lambda x: (x == "Pass").sum()
            ),
            fail_count=(
                "result",
                lambda x: (x == "Fail").sum()
            ),
            average_attendance=(
                "attendance",
                "mean"
            )
        )
        .reset_index()
    )

    result["pass_percentage"] = (
        result["pass_count"]
        /
        (
            result["pass_count"]
            + result["fail_count"]
        )
        * 100
    ).round(2)

    result["average_marks"] = (
        result["average_marks"]
        .round(2)
    )

    result["average_attendance"] = (
        result["average_attendance"]
        .round(2)
    )

    return render_template(
        "subjects.html",
        subjects=result.to_dict(
            orient="records"
        )
    )


# --------------------------------------------------
# CLASSES
# --------------------------------------------------

@app.route("/classes")
@login_required
def classes():

    df = DATA["df"]

    if df is None:

        return redirect(
            url_for("upload")
        )

    result = (
        df.groupby("class")
        .agg(
            students=(
                "student_id",
                "nunique"
            ),
            average_score=(
                "final_score",
                "mean"
            ),
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

    result["pass_percentage"] = (
        result["pass_count"]
        / (result["pass_count"] + result["fail_count"]).replace(0, 1)
        * 100
    ).round(2)
    result["fail_percentage"] = (
        result["fail_count"]
        / (result["pass_count"] + result["fail_count"]).replace(0, 1)
        * 100
    ).round(2)

    # Calculate gender percentages using unique students so that a student
    # appearing in multiple subject rows is counted only once per class.
    student_gender = df[["student_id", "class", "gender"]].drop_duplicates(
        subset=["student_id", "class"]
    ).copy()
    student_gender["gender_normalized"] = (
        student_gender["gender"].astype(str).str.strip().str.lower()
    )
    gender_counts = student_gender.groupby("class").agg(
        gender_total=("student_id", "nunique"),
        male_count=("gender_normalized", lambda x: (x.isin(["male", "m", "man"])).sum()),
        female_count=("gender_normalized", lambda x: (x.isin(["female", "f", "woman"])).sum()),
    ).reset_index()
    result = result.merge(gender_counts, on="class", how="left")
    result["male_percentage"] = (
        result["male_count"] / result["gender_total"].replace(0, 1) * 100
    ).round(2)
    result["female_percentage"] = (
        result["female_count"] / result["gender_total"].replace(0, 1) * 100
    ).round(2)
    result["average_score"] = result["average_score"].round(2)

    return render_template(
        "classes.html",
        classes=result.to_dict(orient="records")
    )


# --------------------------------------------------
# AT RISK
# --------------------------------------------------

@app.route("/at-risk")
@login_required
def at_risk():

    df = DATA["df"]

    if df is None:

        return redirect(
            url_for("upload")
        )

    model_folder = os.path.join(
        app.config["MODEL_FOLDER"],
        "classification"
    )

    model = load_classification_model(
        model_folder,
        "Random Forest"
    )

    if model is None:

        flash(
            "Train the classification model first.",
            "warning"
        )

        return redirect(
            url_for("classification")
        )

    features = [
        "internal_marks",
        "assignment_marks",
        "attendance",
        "previous_score",
        "gender",
        "class",
        "subject"
    ]

    predictions = model.predict(
        df[features]
    )

    probabilities = model.predict_proba(
        df[features]
    )[:, 0]

    result = df.copy()

    result["predicted_result"] = [
        "Pass" if p == 1 else "Fail"
        for p in predictions
    ]

    result["failure_probability"] = (
        probabilities * 100
    ).round(2)

    # Required threshold: > 65%
    risk = result[
        result["failure_probability"] > 65
    ].copy()

    risk["risk_level"] = "HIGH RISK"

    risk["suggested_action"] = (
        "Remedial class and additional practice"
    )

    records = risk[
        [
            "student_id",
            "student_name",
            "class",
            "subject",
            "failure_probability",
            "predicted_result",
            "risk_level",
            "suggested_action"
        ]
    ].to_dict(
        orient="records"
    )

    return render_template(
        "at_risk.html",
        students=records
    )


# --------------------------------------------------
# REPORTS
# --------------------------------------------------

@app.route("/reports")
@login_required
def reports():

    if DATA["df"] is None:

        return redirect(
            url_for("upload")
        )

    return render_template(
        "reports.html"
    )


@app.route(
    "/download/<report_type>"
)
@login_required
def download_report(report_type):

    df = DATA["df"]

    if df is None:

        flash(
            "Upload a dataset first.",
            "warning"
        )

        return redirect(
            url_for("upload")
        )

    try:

        if report_type == "class":

            path = create_class_report(
                df,
                app.config["REPORT_FOLDER"]
            )

        elif report_type == "subject":

            path = create_subject_report(
                df,
                app.config["REPORT_FOLDER"]
            )

        elif report_type == "student":

            path = create_student_report(
                df,
                app.config["REPORT_FOLDER"]
            )

        else:

            flash(
                "Invalid report type.",
                "danger"
            )

            return redirect(
                url_for("reports")
            )

        return send_file(
            path,
            as_attachment=True
        )

    except Exception as error:

        flash(
            str(error),
            "danger"
        )

        return redirect(
            url_for("reports")
        )


# --------------------------------------------------
# RUN
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )