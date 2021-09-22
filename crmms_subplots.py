# -*- coding: utf-8 -*-
"""
Created on Tue Feb 25 10:57:42 2020

@author: buriona
"""

from pathlib import Path
import plotly
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from crmms_utils import get_favicon, get_plotly_js, get_bor_seal


def get_plot_config(img_filename):
    return {
        "modeBarButtonsToRemove": ["sendDataToCloud", "lasso2d", "select2d"],
        "showAxisDragHandles": True,
        "showAxisRangeEntryBoxes": True,
        "displaylogo": False,
        "toImageButtonOptions": {
            "filename": img_filename,
            "width": 1200,
            "height": 700,
        },
    }


def update_layout(fig, site_name, units, initial_rng, date_str, watermark=False):
    seal_image = [
        {
            "source": get_bor_seal(),
            "xref": "paper",
            "yref": "paper",
            "x": 0.5,
            "y": 1.00,
            "sizex": 0.135,
            "sizey": 0.3,
            "yanchor": "bottom",
            "xanchor": "center",
            "opacity": 0.3,
            "layer": "below",
        }
    ]
    annotation = {}
    if watermark:
        annotation = {
            "x": 0.5,
            "y": 0.5,
            "xref": "paper",
            "yref": "paper",
            "text": "<b>SITE UNDER DEVELOPMENT, NOT OFFICIAL</b>",
            "showarrow": False,
            "align": "center",
            "yanchor": "middle",
            "xanchor": "center",
            "font": {"size": 32, "color": "rgba(0,0,0,0.1)"},
            "textangle": -27,
        }
        fig["layout"]["annotations"] += (annotation,)

    fig.update_layout(
        template="plotly_white",
        title_text=(f"<b>{date_str} 24-Month Study and Colorado River Mid-term Modeling System (CRMMS) Modeling Results<br>{site_name}</b>".upper()),
        autosize=True,
        images=seal_image,
        yaxis1=dict(title=dict(text=f"{units[0]}", font=dict(size=11))),
        yaxis2=dict(title=dict(text=f"{units[1]}", font=dict(size=11))),
        yaxis3=dict(title=dict(text=f"{units[2]}", font=dict(size=11))),
        xaxis1=dict(
            type="date",
            tickformat="%b '%y",
            dtick="M3",
            tickangle=-15,
            rangeslider=dict(thickness=0.075, bgcolor="#d8d8d8", visible=False),
            range=initial_rng,
        ),
        xaxis2=dict(
            type="date",
            tickformat="%b '%y",
            dtick="M3",
            tickangle=-15,
            rangeslider=dict(thickness=0.075, bgcolor="#d8d8d8", visible=False),
            range=initial_rng,
        ),
        xaxis3=dict(
            type="date",
            tickformat="%b '%y",
            dtick="M3",
            tickangle=-15,
            rangeslider=dict(thickness=0.075, bgcolor="#d8d8d8", visible=True),
            range=initial_rng,
        ),
        legend={"orientation": "v", "tracegroupgap": 6, "traceorder": "reversed"},
        margin=go.layout.Margin(l=50, r=50, b=5, t=70, pad=5),
        hovermode="x unified",
    )
    return fig


def create_subplot(
    data, site, datatypes, units_dict, chart_dir, date_str, watermark=False
):
    order_dict = {"inflow": 1, "storage": 2, "outflow": 3}
    units = [units_dict[i] for i in order_dict.keys()]
    fig = make_subplots(
        rows=3,
        cols=1,
        subplot_titles=[i.upper() for i in order_dict.keys()],
        shared_xaxes="all",
        vertical_spacing=0.025,
    )
    for titles in fig.layout.annotations:
        y = titles["y"] - 0.02
        titles.update(x=0.035, y=y)

    initial_rng = [None, None]
    for i, traces in enumerate(data):
        curr_datatype = datatypes[i].lower()
        for trace in traces:
            if not curr_datatype == "storage":
                trace.showlegend = False
            if not trace.legendgroup == "crmms CLOUD":
                trace.legendgroup = trace.name
                if trace.name == "24MS MOST PROB":
                    initial_rng[1] = trace.x[24]
                if trace.name == "OBSERVED":
                    initial_rng[0] = trace.x[0]
            fig.append_trace(trace, row=order_dict[curr_datatype], col=1)

    fig = update_layout(fig, site, units, initial_rng, date_str, watermark)
    save_subplot(chart_dir, fig, site)


def save_subplot(chart_dir, fig, site_name):
    img_filename = f"overview_{site_name}"
    chart_filename = "overview.html"
    chart_filepath = Path(chart_dir, chart_filename).as_posix()
    plotly_js = get_plotly_js()
    plotly.offline.plot(
        fig,
        include_plotlyjs=plotly_js,
        config=get_plot_config(img_filename),
        filename=chart_filepath,
        auto_open=False,
    )
    flavicon = f'<link rel="shortcut icon" ' f'href="{get_favicon()}"></head>'
    with open(chart_filepath, "r") as html_file:
        chart_file_str = html_file.read()

    with open(chart_filepath, "w") as html_file:
        html_file.write(chart_file_str.replace(r"</head>", flavicon))


def make_all_subplots(figs, curr_month_dir, date_str, watermark=False):
    site_names = list(set([i["site_name"] for i in figs]))
    print(f"Creating CRMMS Overview charts here: {curr_month_dir}")
    for site in site_names:
        print(f"  Working on {site} - Overview CRMMS Chart")
        site_figs = [i for i in figs if i["site_name"] == site]
        traces = [i["traces"] for i in site_figs]
        datatypes = [i["datatype"].title() for i in site_figs]
        units_dict = {i["datatype"]: i["units"] for i in site_figs}
        chart_dir = site_figs[0]["chart_dir"]
        create_subplot(
            traces, site, datatypes, units_dict, chart_dir, date_str, watermark
        )


if __name__ == "__main__":
    print("write tests please")
