import plotly.express as px

def plot_bar(df, x_col, y_col, title):

    fig = px.bar(
        df,
        x=x_col,
        y=y_col,
        title=title
    )

    return fig