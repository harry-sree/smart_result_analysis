def percentage(value):
    return round(value * 100, 2)


def classification_summary(results):

    summary = []

    for model, metrics in results.items():

        summary.append({
            "model": model,
            "accuracy": percentage(
                metrics["accuracy"]
            ),
            "precision": percentage(
                metrics["precision"]
            ),
            "recall": percentage(
                metrics["recall"]
            ),
            "f1_score": percentage(
                metrics["f1_score"]
            ),
            "confusion_matrix": metrics.get("confusion_matrix", [])
        })

    return summary