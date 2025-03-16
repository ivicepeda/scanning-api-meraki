from fastapi import FastAPI, Request, HTTPException, Response
from typing import Dict, Any
import json
import csv
import os

app = FastAPI()

CSV_FILE = "datosmeraki.csv"
MERAKI_SECRET = os.environ.get("MERAKI_SECRET")

if not MERAKI_SECRET:
    raise ValueError("MERAKI_SECRET environment variable not set")

def initialize_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["clientMac", "seenTime", "location"])

initialize_csv()

@app.post("/meraki_scanning")
async def meraki_scanning(request: Request):
    try:
        meraki_secret_header = request.headers.get("X-Meraki-Signature")
        if not meraki_secret_header or meraki_secret_header != MERAKI_SECRET:
            raise HTTPException(status_code=403, detail="Invalid secret key")

        data: Dict[str, Any] = await request.json()
        process_meraki_data(data)
        return {"status": "success"}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

def process_meraki_data(data: Dict[str, Any]):
    if "data" in data:
        for device in data["data"]:
            client_mac = device.get("clientMac")
            seen_time = device.get("seenTime")
            location = device.get("location", {})
            x = location.get("x")
            y = location.get("y")
            location_str = f"x:{x}, y:{y}"

            if client_mac and seen_time:
                write_to_csv(client_mac, seen_time, location_str)

def write_to_csv(client_mac, seen_time, location):
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([client_mac, seen_time, location])

@app.get("/datos_meraki_csv")
async def get_datos_meraki_csv():
    if not os.path.exists(CSV_FILE):
            raise HTTPException(status_code=404, detail="File Not Found")
    with open(CSV_FILE, mode='r') as file:
        csv_content = file.read()
    os.remove(CSV_FILE)
    initialize_csv()
    return Response(content=csv_content, media_type="text/csv")