# -*- coding: utf-8 -*-
"""
Created on Fri Jul 26 07:55:52 2019

@author: buriona
"""

import sys
import logging
import json
import pandas as pd
import numpy as np
from pathlib import Path
import plotly
from os import makedirs, path
from calendar import monthrange
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
from logging.handlers import TimedRotatingFileHandler
from crmms_charts import get_comp_fig
from crmms_nav import create_nav
from crmms_maps import create_map
from crmms_subplots import make_all_subplots
from crmms_help import create_help_page
from crmms_utils import get_crmms_hdb_site_map, get_crmms_hdb_datatype_map
from crmms_utils import get_favicon, get_plotly_js, get_hdb_alias_map
from crmms_utils import serial_to_trace, is_url_safe
from crmms_utils import res_display_names, print_and_log
from hdb_api.hdb_utils import get_eng_config
from hdb_api.hdb_api import Hdb, HdbTables, HdbTimeSeries


def get_use_datetypes():
    datatypes = [
        "Outflow",
        "Inflow",
        "Pool Elevation",
        "Storage",
        "Outflow_cfs",
        "Inflow_cfs",
    ]

    return [x.lower() for x in datatypes]


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


def create_log(path="crmms_viz_gen.log"):
    logger = logging.getLogger("crmms_viz_gen rotating log")
    logger.setLevel(logging.INFO)

    handler = TimedRotatingFileHandler(path, when="D", interval=28, backupCount=1)

    logger.addHandler(handler)

    return logger


def make_comp_chart(
    df_slot,
    df_obs,
    site_meta,
    chart_filename,
    img_filename,
    date_str,
    watermark=False,
    no_esp=True,
    logger=None,
    plotly_js=None,
):

    if not plotly_js:
        plotly_js = get_plotly_js()
    try:
        site_name = site_meta["site_metadata.site_name"].upper()
        common_name = "datatype_metadata.datatype_common_name"
        datatype_name = f"{site_meta[common_name].upper().replace('VOLUME', '')}"
        fig = get_comp_fig(
            df_slot=df_slot,
            df_obs=df_obs,
            site_name=site_name,
            datatype_name=datatype_name,
            units=units,
            date_str=date_str,
            watermark=watermark,
            no_esp=no_esp,
        )
        plotly.offline.plot(
            fig,
            include_plotlyjs=plotly_js,
            config=get_plot_config(img_filename),
            filename=chart_filename,
            auto_open=False,
        )

        flavicon = f'<link rel="shortcut icon" ' f'href="{get_favicon()}"></head>'
        with open(chart_filename, "r") as html_file:
            chart_file_str = html_file.read()

        with open(chart_filename, "w") as html_file:
            html_file.write(chart_file_str.replace(r"</head>", flavicon))
        return fig

    except Exception as err:
        err_str = (
            f"     Error creating chart - "
            f'{chart_filename.split("flat_files")[-1]} - {err}'
        )
        print_and_log(err_str, logger)


def get_meta(sids, dids):
    tbls = HdbTables
    hdb_alias_list = ["uc"]
    dfs_meta = {}
    sids[:] = [i for i in sids if i]
    dids[:] = [i for i in dids if i]
    for hdb_alias in hdb_alias_list:
        hdb_config = get_eng_config(db=hdb_alias)
        hdb = Hdb(hdb_config)
        df_temp = tbls.sitedatatypes(hdb, sid_list=sids, did_list=dids)
        dfs_meta[hdb_alias] = df_temp

    return dfs_meta["uc"]


def get_model_data(sdi, hdb_alias, model_id, datatype_str, t1, t2):
    ts = HdbTimeSeries
    hdb_config = get_eng_config(db=hdb_alias)
    hdb = Hdb(hdb_config)
    df = ts.series(
        hdb, sdi=sdi, mrid=model_id, label_overide=datatype_str, t1=t1, t2=t2
    )
    return df


def get_real_data(sdi, hdb_alias, datatype_str, t1, t2):
    ts = HdbTimeSeries
    hdb_config = get_eng_config(db=hdb_alias)
    hdb = Hdb(hdb_config)
    df = ts.series(hdb, sdi=sdi, label_overide=datatype_str, t1=t1, t2=t2)
    return df


def make_csv(df, csv_filename, logger=None):
    try:
        df.to_csv(csv_filename, index=True)
    except Exception as err:
        csv_err = f"Error saving {csv_filename} - {err}"
        print_and_log(csv_err, logger)


def make_json(df, json_filename, logger):
    try:
        df.to_json(json_filename, orient="split", index=True)
    except Exception as err:
        json_err = f"Error saving {json_filename} - {err}"
        print_and_log(json_err, logger)


def make_nav(year_str, data_dir, logger=None):
    try:
        nav_str = create_nav(year_str, data_dir)
        print_and_log(nav_str, logger)
    except Exception as err:
        nav_err = f"Error creating ff_nav.html file for {data_dir} - {err}"
        print_and_log(nav_err, logger)


def make_sitemap(date_str, site_type, df_meta, data_dir, logger=None):

    try:
        map_str = create_map(date_str, site_type, df_meta, data_dir)
        print_and_log(map_str, logger)
    except Exception as err:
        map_err = f"Error creating leaflet map file for {site_type} - {err}"
        print_and_log(map_err, logger)


def map_traces(trace):
    trace_int = int(trace)
    trace_dict = {1: "ESP Max", 2: "ESP Min", 3: "ESP Most"}

    return trace_dict.get(trace_int, str(trace_int - 4 + 1991))


def af_to_cfs(df, date_col="datetime", val_col="value"):
    days = df[date_col].apply(lambda x: monthrange(x.year, x.month)[1])
    conv_factor = days * 1.983
    return df[val_col] / conv_factor


def convert_to_start_of_month(x):
    x = x + np.timedelta64(1, "m")
    month = x.month
    year = x.year
    if month == 1:
        return dt(year - 1, 12, 1)
    return dt(year, month - 1, 1)


def parse_model_ids(model_arg):
    model_ids = model_arg.split(",")
    try:
        if len(model_ids) == 1:
            models = {"max": None, "most": model_ids[0], "min": None}
        elif len(model_ids) == 3:
            models = {"max": model_ids[0], "most": model_ids[1], "min": model_ids[2]}
        else:
            raise Exception
    except Exception as err:
        print(
            f"--models {args.models} is improperly formatted, must be a "
            f"single integer for a MOST only run or list of 3 integers "
            f"seperated by commas for MAX, MOST, MIN runs. - {err}"
        )
        sys.exit(1)
    return models


def get_config(config_name, config_path=None):
    if not path.isfile(config_path):
        print(f'"{config_path}" is not a valid filepath, try again.')
        sys.exit(1)
    with Path(config_path).open("r") as pub_config:
        all_configs = json.load(pub_config)
    config = all_configs.get(config_name, None)
    if config:
        pub_name = config.get("name", "UNKNOWN_PUB_DATE")
        models = config.get("mrids", {"max": None, "most": None, "min": None})
        data_filename = config.get("data", DEFAULT_DATA_PATH)
    else:
        print(f'"{args.config}" not found in {config_path}, try again.')
        sys.exit(1)
    return {"name": pub_name, "mrids": models, "data": data_filename}


def set_ouput_path(output_path):
    if not path.exists(args.output):
        print(
            f"--output {args.output} does not exist, "
            f"can not save files there, try again."
        )
        sys.exit(1)
    return Path(args.output).resolve().as_posix()


def check_suite_name(suite_name):
    if is_url_safe(suite_name) is not True:
        print(
            f"The --name {args.name} contains the unsafe url character - , "
            f"{is_url_safe(args.name)}. Please try a different folder name."
        )
        sys.exit(1)
    return suite_name


def get_date_str(suite_name):
    try:
        date_arr = [int(i) for i in suite_name.split("_")]
        date_str = f"{dt(date_arr[1], date_arr[0], 1):%B %Y}"
    except Exception:
        date_str = f"{suite_name}"
    return date_str


def get_year_str(suite_name):
    try:
        date_arr = [int(i) for i in suite_name.split("_")]
        year_str = f"{date_arr[1]}"
    except Exception:
        year_str = f"{suite_name}"
    return year_str


def get_csv_path(csv_path):
    data_path = args.data
    if not path.exists(data_path) or not data_path.endswith(".csv"):
        data_path = path.join(this_dir, "data", data_path)
        if not path.exists(data_path) or not data_path.endswith(".csv"):
            print(
                f"--data {data_path} does not exist, "
                f"please verify location on output .csv, try again."
            )
            sys.exit(1)
    return Path(data_path).resolve()


def get_args():

    cli_desc = "Creates visualization suite for CRMMS results"
    parser = argparse.ArgumentParser(description=cli_desc)
    parser.add_argument(
        "-V", "--version", help="show program version", action="store_true"
    )
    parser.add_argument(
        "-P",
        "--provisional",
        help="watermarks charts with provisional disclaimer",
        action="store_true",
    )
    parser.add_argument(
        "-o", "--output", help="override default output folder", default="local"
    )
    parser.add_argument(
        "--config_path",
        help=f"path to crmms_viz.config, used to overide deafault local one ({DEFAULT_CONFIG_PATH})",
        default=DEFAULT_CONFIG_PATH,
    )
    parser.add_argument(
        "-c",
        "--config",
        help="key to be used in crmms_viz.config, overrides --name, --models, and --data",
    )
    parser.add_argument(
        "-n",
        "--name",
        help="override the default current date based folder name should take form m_YYYY, i.e. 7_2020",
    )
    parser.add_argument(
        "-m",
        "--models",
        help="override models.config, use form: MAX, MOST, MIN. If only one provided it is assumed to be most.",
    )
    parser.add_argument(
        "-d", "--data", help=f"override default data path ({DEFAULT_DATA_PATH})"
    )
    parser.add_argument(
        "--no_esp",
        help="use/show ensemble results in creation of suite",
        action="store_true",
    )
    return parser.parse_args()


if __name__ == "__main__":

    import argparse

    this_dir = Path().absolute()
    DEFAULT_DATA_PATH = Path(this_dir, "data", "ESPcsvOutput.csv")
    DEFAULT_CONFIG_PATH = Path(this_dir, "configs", "crmms_viz.config")

    args = get_args()

    if args.version:
        print("crmms_viz_gen.py v1.0")

    watermark = False
    if args.provisional:
        watermark = True

    if args.config:
        config_dict = get_config(args.config, args.config_path)
        args.name = config_dict["name"]
        args.models = config_dict["mrids"]
        args.data = config_dict["data"]

    if args.data:
        data_path = get_csv_path(args.data)
    else:
        data_path = Path(DEFAULT_DATA_PATH).resolve()

    if args.models:
        if isinstance(args.models, dict):
            models = args.models
        else:
            models = parse_model_ids(args.models)
    else:
        model_config_path = Path("models.config").resolve()
        with model_config_path.open("r") as mrid_config:
            models = json.load(mrid_config)

    now_utc = dt.utcnow()

    if not args.output == "local":
        crmms_viz_dir = set_ouput_path(args.output)
        print(crmms_viz_dir)
    else:
        crmms_viz_dir = Path(this_dir, "crmms_viz").as_posix()
        makedirs(crmms_viz_dir, exist_ok=True)

    if args.name:
        curr_month_str = check_suite_name(args.name)
        date_str = get_date_str(curr_month_str)
        year_str = get_year_str(curr_month_str)
    else:
        curr_month_str = f"{now_utc.month}_{now_utc.year}"
        date_str = f"{now_utc:%b %Y} CRMMS Modeling Results"
        year_str = f"{now_utc:%Y} CRMMS Modeling Results"

    curr_month_dir = Path(crmms_viz_dir, curr_month_str).as_posix()
    makedirs(curr_month_dir, exist_ok=True)

    meta_filepath = Path(curr_month_dir, "meta.csv").as_posix()
    log_dir = Path(this_dir, "logs")
    makedirs(log_dir, exist_ok=True)
    logger = create_log(Path(log_dir, "crmms_viz_gen.log"))

    col_names = ["run", "trace", "obj.slot", "datetime", "value", "unit"]
    dtypes = {
        "Run Number": np.int64,
        "Trace Number": np.int64,
        "Object.Slot": str,
        "Timestep": str,
        "Slot Value": float,
        "Unit": str,
    }

    # this is crmms-esp csv data
    df = pd.read_csv(
        data_path, dtype=dtypes, parse_dates=["Timestep"], infer_datetime_format=True
    )
    header_row = list(dtypes.keys())
    rename_map = {header_row[i]: v for i, v in enumerate(col_names)}
    obj_slot = df["Object.Slot"].str.split(".", 1, expand=True)
    df = df.rename(columns=rename_map)
    df = df.drop(["run"], axis="columns")
    df["obj"] = obj_slot[0]
    df["slot"] = obj_slot[1]

    sids_map = get_crmms_hdb_site_map()
    dids_map = get_crmms_hdb_datatype_map()
    sids = list(set([sids_map[x] for x in df["obj"].unique() if x in sids_map.keys()]))
    dids = list(set([dids_map[x] for x in df["slot"].unique() if x in dids_map.keys()]))
    df["trace"] = df["trace"].apply(lambda x: map_traces(x))
    df_meta = get_meta(sids, dids)
    make_csv(df_meta, meta_filepath, logger)
    use_datatypes = get_use_datetypes()
    hdb_alias_map = get_hdb_alias_map()

    msg = f"Creating CRMMS charts here: {curr_month_dir}"
    print_and_log(msg, logger)
    figs = []
    for slot in list(df["obj.slot"].unique()):
        site_name, datatype_name = slot.split(".")
        units = df[df["obj.slot"] == slot]["unit"].iloc[0]
        if datatype_name.lower() not in use_datatypes:
            continue
        if site_name.lower() not in [x.lower() for x in hdb_alias_map.keys()]:
            continue
        sid = str(sids_map[site_name])
        did = str(dids_map[datatype_name])
        sdi = None
        sdi_series = None
        if sid and did:
            sdi_series = df_meta[
                (df_meta["datatype_id"] == did) & (df_meta["site_id"] == sid)
            ]["site_datatype_id"]
            if not sdi_series.empty:
                sdi = str(sdi_series.iloc[0])
        chart_dir = Path(curr_month_dir, f"{sid}", "charts")
        makedirs(chart_dir, exist_ok=True)
        csv_dir = Path(curr_month_dir, f"{sid}", "csv")
        makedirs(csv_dir, exist_ok=True)
        json_dir = Path(curr_month_dir, f"{sid}", "json")
        makedirs(json_dir, exist_ok=True)
        df_slot = df[df["obj.slot"] == slot][["value", "datetime", "trace"]]
        df_slot["datetime"] = df_slot["datetime"].apply(
            lambda x: convert_to_start_of_month(x)
        )
        if "1000" in units:
            df_slot["value"] = df_slot["value"] * 1000
            units = units.replace("1000 ", "")
        datatype_lower = datatype_name.lower()
        img_filename = f"{sid}_{datatype_lower}"
        chart_filename = f"{datatype_lower}.html"
        chart_filepath = Path(chart_dir, chart_filename).as_posix()
        csv_filename = f"{did}.csv"
        csv_filepath = Path(csv_dir, csv_filename).as_posix()
        json_filename = f"{did}.json"
        json_filepath = Path(json_dir, json_filename).as_posix()

        if sdi:
            try:
                date_arr = args.name.split("_")
                s_year = date_arr[-1]
                s_month = date_arr[0]
                t1 = dt(int(s_year), int(s_month), 1)
            except Exception:
                t1 = min(df_slot["datetime"])

            t2 = t1 + relativedelta(months=23)
            df_slot = df_slot[df_slot["datetime"] >= t1]
            #df_slot = df_slot[df_slot["datetime"] <= t1 + relativedelta(years=5)]
            hdb_alias = hdb_alias_map[site_name]
            display_name = res_display_names()[site_name]
            for model_type, model_id in models.items():
                if model_id:
                    df_model = get_model_data(
                        sdi=sdi,
                        hdb_alias=hdb_alias,
                        model_id=model_id,
                        datatype_str="value",
                        t1=t1,
                        t2=t2,
                    )
                    if not df_model.empty:
                        df_model["datetime"] = df_model.index
                        last_24ms_date = df_model['datetime'].max()
                        # trim the crmms-esp data to match the length of the 24ms data
                        df_slot = df_slot[df_slot['datetime'] <= last_24ms_date]
                        df_model["trace"] = f"24MS {model_type.upper()} PROB"

                        df_slot = df_slot.append(
                            df_model, ignore_index=True, sort=False
                        )
                    else:
                        # but if there is no 24ms data, then just trim to 2 years of data
                        df_slot = df_slot[df_slot['datetime'] <= t1 + relativedelta(years=2)]

            t1_obs = t1 - relativedelta(years=1)
            t2_obs = t1 - relativedelta(months=1)
            df_obs = get_real_data(sdi, hdb_alias, "value", t1_obs, t2_obs)
            if not df_obs.empty:
                df_obs["datetime"] = df_obs.index
                df_obs["trace"] = "OBSERVED"
                df_last_obs = pd.DataFrame(df_slot["trace"].unique(), columns=["trace"])
                df_last_obs["value"] = df_obs.iloc[-1]["value"]
                df_last_obs["datetime"] = df_obs.iloc[-1]["datetime"]

                df_slot = pd.concat(
                    [df_last_obs, df_slot], ignore_index=True, sort=False
                )

        fig = make_comp_chart(
            df_slot=df_slot,
            df_obs=df_obs,
            site_meta=df_meta.loc[sdi],
            chart_filename=chart_filepath,
            img_filename=img_filename,
            date_str=date_str,
            watermark=watermark,
            no_esp=args.no_esp,
            logger=logger,
            plotly_js=None,
        )
        if not datatype_lower == "pool elevation":
            figs.append(
                {
                    "site_name": display_name,
                    "traces": fig["data"],
                    "datatype": datatype_lower,
                    "chart_dir": chart_dir,
                    "units": units,
                }
            )
        df_table = serial_to_trace(df_slot.copy())
        if args.no_esp:
            df_table = df_table[[i for i in df_table.columns if "24MS" in i.upper()]]

        make_csv(df_table, csv_filepath, logger)
        make_json(df_table, json_filepath, logger)
    print("Making subplots...")
    make_all_subplots(figs, curr_month_dir, date_str, watermark)
    print("Making site map...")
    make_sitemap(date_str, curr_month_str, df_meta, crmms_viz_dir, logger)
    print("Making nav...")
    make_nav(year_str, crmms_viz_dir, logger)
    create_help_page(crmms_viz_dir)
