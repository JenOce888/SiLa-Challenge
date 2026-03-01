"""
Dashboard.py
────────────
Live auto-refreshing terminal dashboard built with rich.

"""

from datetime import datetime

from rich import box
from rich.align import Align
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from fetchers.resilience import CircuitBreaker

console = Console()

# Color palette 
# Polar Night  : #2E3440  #3B4252  #434C5E  #4C566A
# Snow Storm   : #D8DEE9  #E5E9F0  #ECEFF4
# Frost        : #8FBCBB  #88C0D0  #81A1C1  #5E81AC
# Aurora       : #BF616A  #D08770  #EBCB8B  #A3BE8C  #B48EAD

NORD = {
    "frost_teal":   "#8FBCBB",
    "frost_sky":    "#88C0D0",
    "frost_blue":   "#81A1C1",
    "frost_navy":   "#5E81AC",
    "aurora_red":   "#BF616A",
    "aurora_orange":"#D08770",
    "aurora_yellow":"#EBCB8B",
    "aurora_green": "#A3BE8C",
    "aurora_purple":"#B48EAD",
    "snow_dim":     "#4C566A",
    "snow_light":   "#D8DEE9",
}


# Header
def _header() -> Panel:
    now = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    content = Text.assemble(
        ("  ASYNC API DASHBOARD\n", f"bold {NORD['frost_sky']}"),
        (f"  {now}  |  Auto-refreshes every 30s", NORD["snow_dim"]),
    )
    return Panel(Align.center(content), style=NORD["frost_navy"], box=box.DOUBLE_EDGE)


# GitHub 
def _github_panel(data: dict) -> Panel:
    user  = data.get("user") or {}
    repos = data.get("repos") or []

    lines: list[str] = []
    if user:
        lines += [
            f"[bold {NORD['snow_light']}]{user.get('name') or user.get('login', 'N/A')}[/bold {NORD['snow_light']}]  "
            f"[{NORD['frost_sky']}]@{user.get('login', '')}[/{NORD['frost_sky']}]",
            f" {user.get('location', 'N/A')}    {user.get('company', 'N/A')}",
            f" [{NORD['aurora_yellow']}]{user.get('public_repos', 0)}[/{NORD['aurora_yellow']}] repos  "
            f" [{NORD['aurora_green']}]{user.get('followers', 0)}[/{NORD['aurora_green']}] followers",
            "",
        ]

    body = Text.from_markup("\n".join(lines)) if lines else Text("")

    if repos:
        table = Table(box=box.SIMPLE_HEAD, show_header=True,
                      header_style=f"bold {NORD['frost_blue']}", expand=True)
        table.add_column("Repository", style=NORD["frost_sky"])
        table.add_column("", justify="right", style=NORD["aurora_yellow"])
        table.add_column("Language",   style=NORD["aurora_purple"])

        for r in repos:
            table.add_row(
                r.get("name", ""),
                str(r.get("stargazers_count", 0)),
                r.get("language") or "—",
            )
        from rich.console import Group
        content = Group(body, table)
    else:
        content = body or Text(f"[{NORD['aurora_red']}]No data available[/{NORD['aurora_red']}]")

    return Panel(content, title=f"[bold {NORD['frost_blue']}]  GitHub[/bold {NORD['frost_blue']}]",
                 border_style=NORD["frost_navy"])


# Weather
def _weather_panel(data: dict | None) -> Panel:
    if not data or data.get("cod") != 200:
        return Panel(
            f"[{NORD['aurora_red']}]Weather — data unavailable[/{NORD['aurora_red']}]",
            title=f"[bold {NORD['frost_teal']}]🌤  Weather[/bold {NORD['frost_teal']}]",
            border_style=NORD["frost_teal"]
        )

    main    = data.get("main", {})
    wind    = data.get("wind", {})
    weather = data.get("weather", [{}])[0]
    city    = data.get("name", "")
    country = data.get("sys", {}).get("country", "")

    content = Text.from_markup(
        f"[bold {NORD['snow_light']}]{city}, {country}[/bold {NORD['snow_light']}]\n"
        f"[{NORD['frost_sky']}]{weather.get('description', '').capitalize()}[/{NORD['frost_sky']}]\n\n"
        f"🌡  Temp     : [{NORD['aurora_yellow']}]{main.get('temp')}°C[/{NORD['aurora_yellow']}]  "
        f"([{NORD['snow_dim']}]feels like {main.get('feels_like')}°C[/{NORD['snow_dim']}])\n"
        f" Humidity  : [{NORD['frost_blue']}]{main.get('humidity')}%[/{NORD['frost_blue']}]\n"
        f"  Wind     : [{NORD['aurora_green']}]{wind.get('speed')} m/s[/{NORD['aurora_green']}]\n"
        f" Pressure  : {main.get('pressure')} hPa\n"
    )
    return Panel(content,
                 title=f"[bold {NORD['frost_teal']}]🌤  Weather[/bold {NORD['frost_teal']}]",
                 border_style=NORD["frost_teal"])


# News
def _news_panel(data: dict | None, query: str) -> Panel:
    if not data or data.get("status") != "ok":
        return Panel(
            f"[{NORD['aurora_red']}]News — data unavailable[/{NORD['aurora_red']}]",
            title=f"[bold {NORD['aurora_green']}]  News[/bold {NORD['aurora_green']}]",
            border_style=NORD["aurora_green"]
        )

    articles = data.get("articles", [])[:5]
    table = Table(box=box.SIMPLE_HEAD, show_header=True,
                  header_style=f"bold {NORD['aurora_green']}", expand=True)
    table.add_column("#", width=3)
    table.add_column("Title",  ratio=3)
    table.add_column("Source", ratio=1, style=NORD["frost_sky"])
    table.add_column("Date",   width=12, style=NORD["snow_dim"])

    for i, article in enumerate(articles, 1):
        title = (article.get("title") or "")
        if len(title) > 65:
            title = title[:65] + "…"
        table.add_row(
            str(i),
            title,
            article.get("source", {}).get("name", "—"),
            (article.get("publishedAt") or "")[:10],
        )

    return Panel(table, title=f"[bold {NORD['aurora_green']}]  News — «{query}»[/bold {NORD['aurora_green']}]",
                 border_style=NORD["aurora_green"])


# API Status Bar (circuit breakers) 
def _status_panel(breakers: dict[str, CircuitBreaker]) -> Panel:
    table = Table(box=box.SIMPLE, show_header=True,
                  header_style=f"bold {NORD['snow_light']}", expand=True)
    table.add_column("API",      style=f"bold {NORD['frost_sky']}")
    table.add_column("State",    justify="center")
    table.add_column("Failures", justify="right", style=NORD["aurora_orange"])

    state_styles = {
        "CLOSED":    (f" CLOSED",    NORD["aurora_green"]),
        "OPEN":      (f" OPEN",      NORD["aurora_red"]),
        "HALF-OPEN": (f" HALF-OPEN", NORD["aurora_yellow"]),
    }

    for name, cb in breakers.items():
        label, color = state_styles.get(cb.state, (cb.state, NORD["snow_light"]))
        table.add_row(name, f"[{color}]{label}[/{color}]", str(cb.failures))

    return Panel(table, title=f"[bold {NORD['snow_dim']}]🔌  Circuit Breakers[/bold {NORD['snow_dim']}]",
                 border_style=NORD["snow_dim"])


# Full Dashboard Layout 
def build_layout(results: dict, breakers: dict[str, CircuitBreaker],
                 query: str) -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(_header(),  size=4, name="header"),
        Layout(name="body"),
        Layout(_status_panel(breakers), size=7, name="footer"),
    )
    layout["body"].split_row(
        Layout(name="left",  ratio=1),
        Layout(name="right", ratio=2),
    )
    layout["left"].split_column(
        Layout(_github_panel(results["github"]),  name="github"),
        Layout(_weather_panel(results["weather"]), name="weather"),
    )
    layout["right"].update(_news_panel(results["news"], query))

    return layout
