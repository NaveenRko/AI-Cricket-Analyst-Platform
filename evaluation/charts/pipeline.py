import plotly.express as px


def plot_pipeline_distribution(df):

    fig = px.pie(

        df,

        names="pipeline",

        values="count",

        title="Pipeline Distribution"

    )

    return fig