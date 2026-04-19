from download_json import download_json
import math
from datetime import datetime, timezone

import pytz
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from twisted.internet import task, reactor
from rich import box
from rich.columns import Columns


console = Console(force_terminal=True, color_system="truecolor")
live = Live(console=console, refresh_per_second=5, screen=True)


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------

def get_tram_data():
    """
    Fetches tram data from tramlive.co.uk for Lace Market (N22),
    merges both directions, filters to the next 30 minutes, and
    returns a list sorted by minutes to arrival.
    """
    api_data = download_json("http://api.tramlive.co.uk/api/N22")
    tram_list = []

    for stop in api_data["stops"]:
        for tram in stop["journeys"]:
            timestamp = tram["timetabled"] / 1000
            arrival_time = datetime.fromtimestamp(timestamp, timezone.utc)
            mins = math.ceil((arrival_time - datetime.now(tz=timezone.utc)).total_seconds() / 60)

            if mins <= 30:
                tram_list.append({
                    "line": tram["line"],
                    "destination": tram["destination"],
                    "mins_to_arrival": mins,
                })

    return sorted(tram_list, key=lambda t: t["mins_to_arrival"])


# ---------------------------------------------------------------------------
# Table builders
# ---------------------------------------------------------------------------

LINE_NAMES = {
    "Line 1": "Toton Lane — Hucknall",
    "Line 2": "Phoenix Park — Clifton",
}

def build_root_train_table(train_tables) -> Table:
    """
    Add all of the train tables to this table
    """
    table = Table(
        box=None,
        show_header=True,
    )
    for train in train_tables:
        table.add_column(train)

    return table

def build_train_table() -> Table:
    """Builds individual table for each 
    train"""
    table = Table(
        show_header=True,
        box=box.SIMPLE_HEAD,
        header_style="bold rgb(255,130,0)",
    )
    table.add_column("22:58", style="bold rgb(255,130,0)")
    table.add_column("Platform 3A", style="bold rgb(255,130,0)")

    table.add_row("Derby","")
    table.add_row("Calling at", "1/1")
    table.add_row("Derby", "22:10")
    table.add_row("", "")
    table.add_row("", "")
    table.add_row("", "")
    table.add_row("", "")
    table.add_row("", "")
    table.add_row("", "")
    table.add_row("", "")
    table.add_row("[green]On Time[/green]", "")
    table.add_row("East Midlands Railway", "")

    return table

def generate_trains():
    trains = [build_train_table() for _ in range(4)]
    return Columns(trains, equal=True, expand=True)

def build_tram_table() -> Table:
    """Builds the main tram departures table."""
    tram_data = get_tram_data()
    now_str = datetime.now(tz=pytz.timezone("Europe/London")).strftime("%H:%M:%S")

    table = Table(
        show_header=True,
        #title="Lace Market Tram Stop",
        header_style="bold magenta",
        caption=f"Updated at {now_str}",
        expand=True,
        padding=0,
        box=box.SIMPLE,
    )
    table.add_column("Line", style="rgb(255,130,0)")
    table.add_column("Destination", style="rgb(255,130,0)")
    table.add_column("Expected", style="rgb(255,130,0)", justify="right")

    for journey in tram_data:
        mins = journey["mins_to_arrival"]
        expected = "Due" if mins <= 0 else f"{mins} min"
        table.add_row(
            LINE_NAMES.get(journey["line"], journey["line"]),
            journey["destination"],
            expected,
        )

    return table


def build_layout() -> Layout:
    """
    Builds the overall screen layout.
    Add more sections here as needed.
    """
    layout = Layout()

    # Top-level split: tram table on the left, placeholder panels on the right
    layout.split_column(
        Layout(name="top", ratio=1),
        Layout(name="trains", ratio=1)
    )

    # Right column can be split into further sections later
    layout["top"].split_row(
        Layout(name="trams"),
        Layout(name="buses"),
    )

    # Populate sections
    layout["trams"].update(Panel(build_tram_table(), title="Trams", border_style="blue"))
    layout["buses"].update(Panel("[dim]Section 2[/dim]", title="Buses", border_style="dim"))
    layout["trains"].update(Panel(generate_trains(), title="Trains", border_style="dim"))

    return layout


# ---------------------------------------------------------------------------
# Refresh callback (called by Twisted every 60 s)
# ---------------------------------------------------------------------------

def refresh():
    """Rebuilds the layout and pushes it to the Live display — no flicker."""
    live.update(build_layout())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

INTERVAL = 60.0  # seconds

live.start()
refresh()  # render immediately on launch

loop = task.LoopingCall(refresh)
loop.start(INTERVAL)
reactor.run()

live.stop()
print(console.color_system)