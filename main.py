from download_json import download_json
import json
from rich.console import Console
from rich.table import Table
from datetime import datetime, timezone
import pytz, os
import math
from twisted.internet import task, reactor

timeout = 60.0 # Sixty seconds

os.system('cls' if os.name == 'nt' else 'clear')
console = Console()
console.clear()

def get_and_display_data():
    data = download_json("http://api.tramlive.co.uk/api/N22")

    pretty = json.dumps(data, indent=2, ensure_ascii=False)
    #print(pretty)
    #print(data['stops'][0]['direction']) #['city']

    table = Table(show_header=True, title="Lace Market Tram Stop", header_style="bold magenta", caption="Updated at {}".format(datetime.now(tz=pytz.timezone('Europe/London')).strftime("%m/%d/%Y, %H:%M:%S")))
    table.add_column("Line", style="dim", width=12)
    table.add_column("Destination")
    table.add_column("Arrival Time")
    table.add_column("Minutes to arrival")

    #PhoenixPark/Hucknall
    for i in data['stops'][0]['journeys']:
        #print("line: {}".format(i['line']))
        #print("destination: {}".format(i['destination']))
        #print("ETA: {}".format(i['timetabled']))
        timestamp = i['timetabled'] / 1000
        #print("ETA: {}".format(datetime.fromtimestamp(timestamp, timezone.utc)))
        arrival_time = datetime.fromtimestamp(timestamp, timezone.utc)
        now = datetime.now(tz=timezone.utc)
        mins_to_arrival = math.ceil((arrival_time - now).total_seconds() / 60)

        if mins_to_arrival < 30 and mins_to_arrival != 0:
            table.add_row(
                i['line'],
                i['destination'],
                datetime.fromtimestamp(timestamp, timezone.utc).astimezone(pytz.timezone('Europe/London')).strftime("%m/%d/%Y, %H:%M:%S"),
                "{} mins".format(str(mins_to_arrival)),
            )
        elif mins_to_arrival == 0:
            table.add_row(
                i['line'],
                i['destination'],
                datetime.fromtimestamp(timestamp, timezone.utc).astimezone(pytz.timezone('Europe/London')).strftime("%m/%d/%Y, %H:%M:%S"),
                "Due",
            )

    #TotonLane/CliftonSouth
    for i in data['stops'][1]['journeys']:
        #print("line: {}".format(i['line']))
        #print("destination: {}".format(i['destination']))
        #print("ETA: {}".format(i['timetabled']))
        timestamp = i['timetabled'] / 1000
        #print("ETA: {}".format(datetime.fromtimestamp(timestamp, timezone.utc)))
        arrival_time = datetime.fromtimestamp(timestamp, timezone.utc)
        now = datetime.now(tz=timezone.utc)
        mins_to_arrival = math.ceil((arrival_time - now).total_seconds() / 60)

        if mins_to_arrival < 30 and mins_to_arrival != 0:
            table.add_row(
                i['line'],
                i['destination'],
                datetime.fromtimestamp(timestamp, timezone.utc).astimezone(pytz.timezone('Europe/London')).strftime("%m/%d/%Y, %H:%M:%S"),
                "{} mins".format(str(mins_to_arrival)),
            )
        elif mins_to_arrival == 0:
            table.add_row(
                i['line'],
                i['destination'],
                datetime.fromtimestamp(timestamp, timezone.utc).astimezone(pytz.timezone('Europe/London')).strftime("%m/%d/%Y, %H:%M:%S"),
                "Due",
            )
    console.clear()
    console.print(table)

l = task.LoopingCall(get_and_display_data)
l.start(timeout) # call every sixty seconds

reactor.run()