from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from typing import TypedDict
from pathlib import Path
import json
import os

from geopy import distance

import urllib.request

import googlemaps

'''
custom_routes_path = Path("../db/custom_routes.json")

reviews_path = Path("../db/reviews.json")
'''
custom_routes_path = Path(__file__).parent.parent/"db/custom_routes.json"

reviews_path = Path(__file__).parent.parent/"db/reviews.json"

app = FastAPI()

origins = [
    "http://localhost:3000",
    "localhost:3000"
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

gmaps = googlemaps.Client(key=os.environ['VITE_MAPS_API_KEY'])

@app.get("/", tags=["root"])
async def read_root() -> dict:
    return {"message": "Welcome to your todo list."}

@app.get("/custom_routes")
async def read_custom_routes(to_lat: float, to_lon: float) -> JSONResponse:
    """
    Finds all custom routes within a 0.5 mile radius of specified lat and lon
    Query: [url]/custom_routes?to_lat=[latitude]&to_lon=[longitude]
    """
    if custom_routes_path.exists():
        file = json.load(open(custom_routes_path))
        file_list = [route for route in file["custom_routes"] if distance.distance((to_lat, to_lon), (route["destination_lat"], route["destination_lon"])).miles <= 0.5]
        return JSONResponse(file_list)
    return JSONResponse({"Error": "File not found"})

@app.get("/reviews")
async def read_reviews(custom: bool, id: str | int) -> JSONResponse:
    """
    Finds all reviews of a route
    If route is through Google Routes, routeId is unique polyline
    If route is custom, routeId is the id associated with custom route
    Query: [url]/reviews?custom=[true/false]&id=[id]
    """
    if reviews_path.exists():
        if id.isdigit():
            id = int(id)
        file = json.load(open(reviews_path))
        file_list = [review for review in file["reviews"] if review["isCustom"] == custom and review["routeId"] == id]
        return JSONResponse(file_list)
    return JSONResponse({"Error": "File not found"})

@app.get("/maps_autocomplete")
async def get_map_autocomplete(input: str) -> JSONResponse:
    '''
    Returns all predicted autocomplete searches on Google Maps
    {
        "description": string
        "place_id": string
    }
    '''
    try:
        request = urllib.request.urlopen(f"https://maps.googleapis.com/maps/api/place/autocomplete/json?key={os.getenv('VITE_MAPS_API_KEY')}&input={input}")
        return request.read().decode(encoding="utf-8")
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as error:
        return JSONResponse({"Error":error})


@app.get("/maps_route")
async def get_map_route(origin: str, destination: str, alternatives: bool = True) -> JSONResponse:
    '''
    Returns best Google Maps route
    '''
    # route = gmaps.directions(origin,destination) 
    # return route
    try:
        request = urllib.request.urlopen(f"https://maps.googleapis.com/maps/api/directions/json?destination={destination}&origin={origin}&alternatives={alternatives}&key={os.environ['VITE_MAPS_API_KEY']}")
        return request.read().decode(encoding="utf-8")
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as error:
        return JSONResponse({"Error":error})