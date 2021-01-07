"""
Methods for training and evaluating models.
"""

import sys
sys.path.append("./")

from haxml.utils import (
    load_match,
    total_scored_goals,
    total_kicks,
    goal_fraction
)
from matplotlib.figure import Figure
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    roc_auc_score,
    mean_absolute_error,
    mean_squared_error
)
from tqdm import tqdm
import warnings


NO_PREDICTED_SAMPLES = "Precision is ill-defined and being set to 0.0 due to no predicted samples. Use `zero_division` parameter to control this behavior"


def summarize_split(metadata):
    """
    Helper method to summarize a train/test split.
    Args:
        metadata: Match metadata for one split (list of dicts).
    """
    goals = sum(total_scored_goals(m) for m in metadata)
    kicks = sum(total_kicks(m) for m in metadata)
    frac = goal_fraction(goals, kicks)
    print("Matches: {:,}".format(len(metadata)))
    print("Goals: {:,}".format(goals))
    print("Kicks: {:,}".format(kicks))
    print("E(XG): {:.3f}".format(frac))


def style_columns(config):
    """
    Styles columns for a DataFrame.
    """
    def style_fn(ser):
        if ser.name not in config:
            return ["" for val in ser]
        styles = []
        col = config[ser.name]
        rgb = col["rgb"]
        for val in ser:
            score = (val - col["low"]) / (col["high"] - col["low"])
            alpha = min(max(0, score), 1)
            css = f"background-color: rgba({rgb}, {alpha})"
            styles.append(css)
        return styles
    return style_fn


def make_df(metadata, stadiums, callback, progress=False):
    """
    Transforms match metadata into a DataFrame of records for
    each kick, including target label and features.
    Args:
        metadata: Match metadata (list of dicts).
        stadiums: Dictionary of stadium data (via haxml.utils.get_stadiums).
        callback: Method to run on each match to extract kicks.
        progress: Whether or not to show progress bar (boolean).
    Returns:
        DataFrame where each row is a kick record.
    """
    rows = []
    bar = tqdm(metadata) if progress else metadata
    for meta in bar:
        key = meta["match_id"]
        infile = "../data/packed_matches/{}.json".format(key)
        try:
            s = stadiums[meta["stadium"]]
            row_gen = load_match(infile, lambda m: callback(m, s))
            for row in row_gen:
                row["match"] = key
                rows.append(row)
        except FileNotFoundError:
            pass
    return pd.DataFrame(rows)


def score_model(d_test, target, features, clf, kwargs):
    """
    Score a given model and return its metrics and metadata.
    Args:
        d_test: DataFrame of test data.
        target: Variable to predict (str).
        features: Columns of DataFrame to use as predictors (list of str).
        clf: Classifier (sklearn style).
        kwargs: Keyword args for classifier.
    Scores:
        accuracy: correct predictions / all records
        precision: true positives / predicted positives
        recall: true positives / actual positives
        roc_auc: area under the ROC curve (0.5 is as good as random)
        match_mae: mean absolute error between XG and AG per match
        match_rmse: root mean squared error between XG and AG per match
        xg_mean: mean of XG on dataset
        xg_std: standard deviation of XG on dataset
    Returns:
        Dictionary with fields for scoring metrics and model metadata.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=NO_PREDICTED_SAMPLES)
        Xt = d_test[features]
        yt = d_test[target]
        xg = clf.predict_proba(Xt)[:,1]
        yp = clf.predict(Xt)
        d_test["xg"] = xg
        gp = d_test.groupby(["match"]).agg({"ag": sum, "xg": sum})
        return {
            "model": type(clf).__name__,
            "features": features,
            "clf": clf,
            "kwargs": kwargs,
            "accuracy": accuracy_score(yt, yp),
            "precision": precision_score(yt, yp),
            "recall": recall_score(yt, yp),
            "roc_auc": roc_auc_score(yt, yp),
            "match_mae": mean_absolute_error(gp["ag"], gp["xg"]),
            "match_rmse": mean_squared_error(gp["ag"], gp["xg"], squared=False),
            "xg_mean": np.mean(xg),
            "xg_std": np.std(xg)
        }


def run_models(d_train, d_test, score_fn, target, feature_sets, model_params):
    """
    Trains and scores models for evaluation.
    Args:
        d_train: DataFrame of train data.
        d_test: DataFrame of test data.
        score_fn: Method to get scoring metrics and metadata for each model.
        target: Variable to predict (str).
        feature_sets: List of lists of strings, where strings are columns of
            DataFrame to use as predictors.
        model_params: List of tuples of (Classifier, kwargs) where Classifier is
            the sklearn Classifier type and kwargs are the keyword args.
    Returns:
        DataFrame of models with their scoring metrics and metadata.
    """
    n_combinations = len(feature_sets) * len(model_params)
    res = []
    with tqdm(total=n_combinations) as bar:
        for features in feature_sets:
            for Classifier, kwargs in model_params:
                clf = Classifier(**kwargs)
                bar.set_description("Model: {}".format(clf))
                bar.refresh()
                X_train = d_train[features]
                y_train = d_train[target]
                X_test = d_test[features]
                y_test = d_test[target]
                clf.fit(X_train, y_train)
                scores = score_fn(d_test, target, features, clf, kwargs)
                res.append(scores)
                bar.update(1)
    return pd.DataFrame(res)


def blank_plot():
    """
    Returns a new tuple of (fig, ax).
    """
    fig = Figure()
    ax = fig.add_subplot(1, 1, 1)
    return fig, ax


def plot_errors_by_kicks(model, d_test, plot=None, kwargs={}):
    """
    Creates scatter plot of XG errors per match by number of kicks.
    """
    if plot is None:
        fig, ax = blank_plot()
    else:
        fig, ax = plot
    name = str(model["clf"])
    feat = ", ".join(model["features"])
    label = f"Model: {name}\nFeatures: {feat}"
    X_test = d_test[model["features"]]
    xg = model["clf"].predict_proba(X_test)[:,1]
    df_pred = pd.DataFrame(d_test)
    df_pred["xg"] = xg
    df_gp = df_pred.groupby("match").agg({"ag": sum, "xg": sum, "index": len})
    ax.scatter(df_gp["index"], df_gp["xg"] - df_gp["ag"], label=label, **kwargs)
    ax.legend(bbox_to_anchor=(1.5, 1), loc="upper right")
    ax.axhline(0, color="black", linewidth=1)
    ax.axvline(0, color="black", linewidth=1)
    ax.set_xlabel("Number of Kicks in Match")
    ax.set_ylabel("XG Error")
    sub = "Negative Error = Underpredicted Actual Goals"
    ax.set_title(f"XG Error per Match by Kicks\n{sub}")
    fig.set_size_inches(10, 6)
    return fig, ax


def plot_errors_by_goals(model, d_test, plot=None, kwargs={}):
    """
    Creates violin plot of XG errors per match by number of goals.
    """
    if plot is None:
        fig, ax = blank_plot()
    else:
        fig, ax = plot
    if not hasattr(ax, "violin_legends"):
        ax.violin_legends = []
    name = str(model["clf"])
    feat = ", ".join(model["features"])
    label = f"Model: {name}\nFeatures: {feat}"
    color = kwargs["color"] if "color" in kwargs else None
    X_test = d_test[model["features"]]
    xg = model["clf"].predict_proba(X_test)[:,1]
    df_pred = pd.DataFrame(d_test)
    df_pred["xg"] = xg
    df_gp = df_pred.groupby("match").agg({"ag": sum, "xg": sum})
    violins = {}
    for match in df_gp.to_dict(orient="records"):
        ag = match["ag"]
        error = match["xg"] - match["ag"]
        if ag not in violins:
            violins[ag] = []
        violins[ag].append(error)
    # S/O: https://stackoverflow.com/questions/33864578/matplotlib-making-labels-for-violin-plots
    violin = ax.violinplot(violins.values(), violins.keys(), showextrema=False)
    if color:
        for part in violin["bodies"]:
            part.set_facecolor(color)
            part.set_edgecolor(color)
    color = violin["bodies"][0].get_facecolor().flatten()
    ax.violin_legends.append((mpatches.Patch(color=color), label))
    labels = zip(*ax.violin_legends)
    ax.legend(*labels, bbox_to_anchor=(1.5, 1), loc="upper right")
    ax.axhline(0, color="black", linewidth=1)
    ax.set_xlabel("Actual Goals in Match")
    ax.set_ylabel("XG Error")
    sub = "Negative Error = Underpredicted Actual Goals"
    ax.set_title(f"XG Error per Match by Goals\n{sub}")
    fig.set_size_inches(10, 6)
    return fig, ax


def plot_xg_histogram(model, d_test, plot=None, kwargs={}, min_xg=1e-4):
    """
    Creates histogram plot of XG per kick.
    """
    if plot is None:
        fig, ax = blank_plot()
    else:
        fig, ax = plot
    name = str(model["clf"])
    feat = ", ".join(model["features"])
    label = f"Model: {name}\nFeatures: {feat}"
    X_test = d_test[model["features"]]
    xg = model["clf"].predict_proba(X_test)[:,1]
    ax.hist(list(filter(lambda v: v > min_xg, xg)), label=label, **kwargs)
    ax.legend(bbox_to_anchor=(1.5, 1), loc="upper right")
    ax.set_xlabel("XG")
    ax.set_ylabel("Number of Kicks")
    ax.set_title("XG Histogram")
    fig.set_size_inches(10, 6)
    return fig, ax
