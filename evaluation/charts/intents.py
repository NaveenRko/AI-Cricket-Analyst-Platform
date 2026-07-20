import plotly.express as px


def plot_intents(df):

    fig = px.bar(

        df,

        x="count",

        y="intent",

        orientation="h",

        title="Intent Distribution"

    )

    return fig