import plotly.express as px


def plot_query_trend(df):

    fig = px.line(

        df,

        x="timestamp",

        y="queries",

        markers=True,

        title="Query Trend"

    )

    fig.update_layout(

        xaxis_title="Time",

        yaxis_title="Queries"

    )

    return fig