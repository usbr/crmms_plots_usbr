# -*- coding: utf-8 -*-
"""
Created on Wed May 22 12:08:25 2019

@author: buriona
"""

from pathlib import Path, PurePath
from hdb_api.hdb_utils import datatype_units, datatype_common_names
from crmms_utils import get_bor_seal, map_dids
from crmms_utils import get_html_head, get_js_refs

SKIP_DATA_LINKS = ["overview"]

label_unit_dict = {
    datatype_common_names[i]: datatype_units[i] for i in datatype_units.keys()
}

datatype_common_names_rev = {v: k for k, v in datatype_common_names.items()}
bor_seal = get_bor_seal()


def get_feather(datatype_name):
    units = label_unit_dict.get(datatype_name, "UNKNOWN UNITS").lower()
    if units in ["acre-ft"] and "storage" not in datatype_name.lower():
        return "bar-chart-2"
    elif units == "UNKNOWN UNITS":
        return "chevron-right"
    return "trending-up"


def get_datatype_units(datatype_id, datatype_units_dict):
    units = datatype_units_dict.get(datatype_id, "UNKNOWN UNITS")
    return units


def get_site_url():
    return "https://www.usbr.gov/uc/water/index.html"


def get_home_url():
    return r"../../crmms_nav.html"


def get_map_url():
    return r"../site_map.html"


def create_sidebar_link(chart_name, feather):
    jumpto = chart_name.replace(" ", "_")
    label = jumpto.title().replace("_", " ")
    link = f"""          <li class="nav-item">
            <a class="nav-link" data-toggle="tab" href="#{jumpto}" role="tab">
            <span data-feather="{feather}"></span>  {label}</a>
          </li>"""
    return link


def get_chart_navbar_links(chart_names):
    navbar_links = []
    for chart_name in sorted(
        chart_names, key=lambda x: x if not x.lower() == "overview" else "0"
    ):
        feather = get_feather(chart_name.replace("_", " "))
        nav_link = create_sidebar_link(chart_name, feather)
        if chart_name == "overview":
            nav_link = nav_link.replace("nav-link", "nav-link active")
        navbar_links.append(nav_link)
    return "\n".join(navbar_links)


def create_embed(chart_name):
    jumpto = chart_name.replace(" ", "_")
    embed = f"""          <div id="{jumpto}" class="tab-pane fade in embed-responsive embed-responsive-16by9" role="tabpanel">
            <embed class="embed-responsive-item" src="./charts/{chart_name}.html" scrolling="no" frameborder="0" allowfullscreen></embed>
          </div>"""
    return embed


def get_embeds(chart_names):
    embeds = []
    for chart_name in chart_names:
        embed = create_embed(chart_name)
        if chart_name == "overview":
            embed = embed.replace("tab-pane", "tab-pane active show")
        embeds.append(embed)
    return "\n".join(embeds)


def create_data_link(chart_name, file_type):
    if chart_name.lower() in SKIP_DATA_LINKS:
        return ""
    data_type = map_dids(chart_name.title())
    ext = file_type.lower()
    label = chart_name.title().replace("_", " ")
    return f"""                <a href="./{ext}/{data_type}.{ext}">
                  <li class="list-group-item d-flex justify-content-between align-items-center">{label}
                    <span class="badge badge-primary badge-pill">{ext}</span>
                  </li>
                </a>"""


def get_data_div(chart_names, file_type):
    jumpto = file_type.lower()
    prefix = f"""
          <div id="{jumpto}" class="tab-pane fade in col-sm-4 col-md-3 m-5" role="tabpanel">
            <embed class="embed-responsive-item">
              <ul class="list-group">
"""
    data_div = []
    for chart_name in chart_names:
        data_div.append(create_data_link(chart_name, file_type))
    body = "\n".join(data_div)
    return f"""{prefix}{body}
              </ul>
            </embed>
          </div>"""


def get_dash_body(site_name, site_id, chart_names):
    return f"""
<body>
<nav class="navbar navbar-light fixed-top bg-light navbar-expand p-auto flex-md-nowrap">
  <a class="btn btn-outline-primary" target="_blank" href="#overview">{site_name}
    <i class="fa fa-external-link" aria-hidden="true"></i>
  </a>
  <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav">
  <span class="navbar-toggler-icon"></span>
  </button>
  <div class="collapse navbar-collapse" id="navbarNav">
    <ul class="navbar-nav  mr-auto">
      <li class="nav-item">
        <a class="nav-link-primary ml-3" href="{get_map_url()}" target="_blank">Basin Map</a>
        </li>
      <li class="nav-item dropdown">
        <a class="nav-link-primary ml-3 dropdown-toggle" href="#" id="navbarDropdown" role="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
        Jump to Reservoir...
        </a>
        <div class="dropdown-menu" aria-labelledby="navbarDropdown">
          <a class="dropdown-item" href="../913/dashboard.html#overview" target="_blank">Blue Mesa</a>
          <a class="dropdown-item" href="../915/dashboard.html#overview" target="_blank">Crystal</a>
          <a class="dropdown-item" href="../917/dashboard.html#overview" target="_blank">Flaming Gorge</a>
          <a class="dropdown-item" href="../916/dashboard.html#overview" target="_blank">Fontenelle</a>
          <a class="dropdown-item" href="../923/dashboard.html#overview" target="_blank">Lake Havasu</a>
          <a class="dropdown-item" href="../921/dashboard.html#overview" target="_blank">Lake Mead</a>
          <a class="dropdown-item" href="../922/dashboard.html#overview" target="_blank">Lake Mohave</a>
          <a class="dropdown-item" href="../914/dashboard.html#overview" target="_blank">Morrow Point</a>
          <a class="dropdown-item" href="../920/dashboard.html#overview" target="_blank">Navajo</a>
          <a class="dropdown-item" href="../919/dashboard.html#overview" target="_blank">Lake Powell</a>
          <a class="dropdown-item" href="../912/dashboard.html#overview" target="_blank">Taylor Park</a>
          <a class="dropdown-item" href="../933/dashboard.html#overview" target="_blank">Vallecito</a>
        </div>
      </li>
      <li class="nav-item">
        <a class="nav-link-primary ml-3" href="{get_home_url()}" target="_blank">Other Studies</a>
      </li>
    </ul>
  </div>
</nav>
<div class="container-fluid">
  <div class="row">
    <nav class="sidebar col-md-2 mt-2">
      <div class="sidebar-sticky">
        <a class="sidebar-heading d-flex px-3 mt-4 mb-1" href="https://www.usbr.gov/uc/water/index.html">
          <img src="{bor_seal}" class="img-fluid" alt="Reclamation Seal">
        </a>
        <ul class="nav flex-column nav-tabs" id="navTabs" role="tablist">
         <h6 class="sidebar-heading d-flex justify-content-between align-items-center px-3 mt-4 mb-1 text-muted">
           <span>Charts</span>
           <a class="d-flex align-items-center text-muted" href="#">
             <span data-feather="trending-up"></span>
             <span data-feather="bar-chart-2"></span>
           </a>
         </h6>
         {get_chart_navbar_links(chart_names)}
         <h6 class="sidebar-heading d-flex justify-content-between align-items-center px-3 mt-4 mb-1 text-muted">
           <span>Download Data</span>
           <a class="d-flex align-items-center text-muted" href="#">
             <span data-feather="database"></span>
             <span data-feather="archive"></span>
           </a>
         </h6>
         <li class="nav-item">
           <a class="nav-link" data-toggle="tab" href="#csv" role="tab">
             <span data-feather="database"></span>  CSV DATA</a>
         </li>
         <li class="nav-item">
           <a class="nav-link" data-toggle="tab" href="#json"  role="tab">
             <span data-feather="archive"></span>  JSON DATA</a>
         </li>
         <h6 class="sidebar-heading d-flex justify-content-between align-items-center px-3 mt-4 mb-1 text-muted">
           <span>Help and Links</span>
           <a class="d-flex align-items-center text-muted" href="#">
             <span data-feather="help-circle"></span>
           </a>
         </h6>
         <li class="nav-item">
           <a class="nav-link" data-toggle="tab" href="#help" role="tab">
             <span data-feather="help-circle"></span> PLOT DESCRIPTION</a>
         </li>
         <li class="nav-item">
           <a class="nav-link" href="https://www.usbr.gov/lc/region/g4000/riverops/model-info.html#overview_m" role="tab">
             <span data-feather="help-circle"></span> WHAT IS CRMMS?</a>
         </li>
         <li class="nav-item">
           <a class="nav-link" href="https://www.usbr.gov/lc/region/g4000/riverops/model-info.html#future" role="tab">
             <span data-feather="help-circle"></span> WHAT IS ESP?</a>
         </li>
         <li class="nav-item">
           <a class="nav-link" href="https://www.usbr.gov/lc/region/g4000/riverops/crss-5year-projections.html" role="tab">
             <span data-feather="trending-up"></span> 5-YEAR PROJECTIONS</a>
         </li>
        </ul>
      </div>
    </nav>
    <main class="col-md-9 ml-sm-auto col-lg-10 px-1 pt-5">
        <div class="row tab-content m-auto p-auto">
{get_embeds(chart_names)}
{get_data_div(chart_names, 'csv')}
{get_data_div(chart_names, 'json')}
          <div id="help" class="tab-pane fade in embed-responsive embed-responsive-16by9" role="tabpanel">
            <embed class="embed-responsive-item" src="../../help.html" scrolling="no" frameborder="0" allowfullscreen></embed>
          </div>
        </div>
    </main>
  </div>
</div>

{get_js_refs()}

</body>
</html>
"""


def create_dash(site_name, site_id, site_path):
    chart_dir = Path(site_path, "charts").resolve()
    chart_paths = chart_dir.iterdir()
    chart_names = [PurePath(x) for x in chart_paths]
    chart_names[:] = [x for x in chart_names if x.suffix == ".html"]
    chart_names[:] = [x.name.replace(".html", "") for x in chart_names]
    return f"{get_html_head()}{get_dash_body(site_name, site_id, chart_names)}"


if __name__ == "__main__":

    from crmms_nav import create_nav

    this_dir = Path().absolute()
    data_dir = Path(this_dir, "crmms_viz")
    sys_out = create_nav(data_dir)
    print(sys_out)
