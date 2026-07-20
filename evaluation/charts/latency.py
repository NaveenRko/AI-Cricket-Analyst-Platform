import plotly.express as px


def plot_latency(df):

    fig = px.line(

        df,

        x="timestamp",

        y="avg_latency",

        markers=True,

        title="Average Response Time"

    )

    fig.update_layout(

        yaxis_title="Seconds"

    )

    return fig