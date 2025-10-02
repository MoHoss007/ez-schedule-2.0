import os
import logging
from typing import Any, Dict, Optional
import requests
from requests.exceptions import RequestException
from app.clients.exceptions import GoogleAPIError
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class GoogleClient:
    GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
    MAPS_URL_TEMPLATE = "https://www.google.com/maps/place/?q=place_id:{place_id}"
    NEARBY_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

    def __init__(self, api_key: Optional[str] = None) -> None:
        if api_key:
            self.api_key = api_key
        else:
            load_dotenv()
            self.api_key = os.getenv("GOOGLE_API_KEY")

        if not self.api_key:
            raise ValueError(
                "Google API key not provided; set GOOGLE_API_KEY in environment or pass it explicitly."
            )

    def get_address(self, city_name: str, place: str) -> Dict[str, Any]:
        """
        Use Google’s Geocoding API to turn “place + city” into:
          - formatted_address
          - geometry.location {lat, lng}
          - place_id
          - a Google Maps URL

        :param city_name: e.g. "Toronto"
        :param place:     e.g. "CN Tower"
        :return:          Dict with those keys
        :raises GoogleAPIError: on network, JSON, or API‐status errors
        """
        query = f"{place}, {city_name}"
        params = {
            "address": query,
            "key": self.api_key,
        }

        # 1) Network / HTTP errors
        try:
            resp = requests.get(self.GEOCODE_URL, params=params, timeout=10)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.error("HTTP request failed: %s", e)
            raise GoogleAPIError(f"Network error while fetching geocode: {e}")

        # 2) JSON parse errors
        try:
            data = resp.json()
        except ValueError as e:
            logger.error("JSON parse failed: %s", e)
            raise GoogleAPIError("Invalid JSON response from Geocoding API")

        # 3) API‐level errors
        status = data.get("status")
        if status != "OK":
            err_msg = data.get("error_message") or status
            logger.warning("Geocoding API error %s: %s", status, err_msg)
            raise GoogleAPIError(f"Geocoding API error: {status} – {err_msg}")

        results = data.get("results", [])
        if not results:
            logger.info("No geocode results for query %r", query)
            raise GoogleAPIError(f"No address found for '{query}'")

        # Take the first result
        res = results[0]
        formatted_address = res.get("formatted_address")
        location = res.get("geometry", {}).get("location", {})
        place_id = res.get("place_id")

        if not place_id:
            raise GoogleAPIError("No place_id returned by Geocoding API")

        # Build the Maps URL
        map_url = self.MAPS_URL_TEMPLATE.format(place_id=place_id)

        return {
            "formatted_address": formatted_address,
            "location": location,
            "place_id": place_id,
            "maps_url": map_url,
        }

    def find_nearest_soccer_field(self, city_name: str, place: str) -> Dict[str, Any]:
        """
        Find the closest 'soccer field' near the given place in the city,
        returning the same keys as get_address.
        """
        # 1) Get the base location
        base = self.get_address(city_name, place)
        lat, lng = base["location"]["lat"], base["location"]["lng"]

        params = {
            "location": f"{lat},{lng}",
            "rankby": "distance",
            "keyword": "soccer field",
            "key": self.api_key,
        }

        # 2) HTTP / network
        try:
            resp = requests.get(self.NEARBY_SEARCH_URL, params=params, timeout=10)
            resp.raise_for_status()
        except requests.RequestException as e:
            logger.error("Nearby search request failed: %s", e)
            raise GoogleAPIError(f"Network error during nearby search: {e}")

        # 3) JSON parse
        try:
            data = resp.json()
        except ValueError as e:
            logger.error("Nearby search JSON parse failed: %s", e)
            raise GoogleAPIError("Invalid JSON from Places Nearby Search")

        # 4) API‐status
        status = data.get("status")
        if status == "ZERO_RESULTS":
            raise GoogleAPIError(f"No soccer field found near '{place}, {city_name}'")
        if status != "OK":
            err = data.get("error_message") or status
            logger.warning("Places API error %s: %s", status, err)
            raise GoogleAPIError(f"Places API error: {status} – {err}")

        results = data.get("results", [])
        if not results:
            raise GoogleAPIError(f"No soccer field results for '{place}, {city_name}'")

        # 5) Build output from the first (closest) result
        field = results[0]
        pid = field["place_id"]
        name = field.get("name", "")
        vic = field.get("vicinity", "")
        addr = f"{name}, {vic}" if vic else name

        return {
            "formatted_address": addr,
            "location": field["geometry"]["location"],
            "place_id": pid,
            "maps_url": self.MAPS_URL_TEMPLATE.format(place_id=pid),
        }
