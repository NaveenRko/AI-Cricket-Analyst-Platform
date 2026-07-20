import pandas as pd


def prepare_metrics(df):

    trend = (
        df
        .groupby(df["timestamp"].dt.floor("h"))
        .size()
        .reset_index(name="queries")
    )

    pipeline = (
        df["pipeline_eval"]
        .fillna("unknown")
        .value_counts()
        .reset_index()
    )

    pipeline.columns = [

        "pipeline",

        "count"

    ]

    intents = (

        df["agent_selected"]

        .value_counts()

        .reset_index()

    )

    intents.columns = [

        "intent",

        "count"

    ]

    latency = (

        df

        .groupby(df["timestamp"].dt.floor("h"))["response_time"]

        .mean()

        .reset_index()

    )

    latency.columns = [

        "timestamp",

        "avg_latency"

    ]

    return {

        "trend": trend,

        "pipeline": pipeline,

        "intents": intents,

        "latency": latency

    }