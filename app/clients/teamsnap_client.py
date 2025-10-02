from typing import Optional, Dict, Any, List
import requests
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class TeamSnapClient:
    def __init__(self, bearer_token: str, base_url: str):
        self.base_url: str = base_url.rstrip("/")
        self.headers: Dict[str, str] = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
        }

    def _get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        url: str = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    def _post(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        url: str = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    def _put(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        url: str = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.put(url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    def _delete(self, endpoint: str) -> Dict[str, Any]:
        url: str = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.delete(url, headers=self.headers)
            response.raise_for_status()
            return {"success": True}
        except requests.RequestException as e:
            return {"error": str(e)}

    def _patch(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        url: str = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.patch(url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    def update_game(self, event_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Updates an existing game with the provided event data.
        """
        endpoint = f"/events/{event_id}"
        return self._put(endpoint, data=event_data)

    def delete_game(self, event_id: str) -> Dict[str, Any]:
        """
        Deletes a game by its ID.
        """
        endpoint = f"/events/{event_id}"
        return self._delete(endpoint)

    def get_registered_teams(self) -> Dict[str, List[int]]:
        """
        Fetches the list of managed team IDs for the current user.
        """
        response = self._get("/me")

        try:
            # Grab the first user item
            user_data = response["collection"]["items"][0]["data"]

            # Convert it to a dictionary for easy access
            data_dict = {item["name"]: item["value"] for item in user_data}

            managed_teams = data_dict.get("managed_team_ids", [])
            return {"registered_teams": managed_teams}
        except (KeyError, IndexError, TypeError):
            return {"registered_teams": []}

    def get_user_id(self) -> Optional[str]:
        """
        Fetches the TeamSnap user ID of the current user.
        """
        response = self._get("/me")

        try:
            user_data = response["collection"]["items"][0]["data"]
            data_dict = {item["name"]: item["value"] for item in user_data}
            return data_dict.get("id")
        except (KeyError, IndexError, TypeError):
            return None

    def get_team_info(self, team_id: str) -> Dict[str, Any]:
        """
        Fetches information about a specific team and returns the team name.
        """
        response = self._get(f"/teams/{team_id}")

        try:
            data = response["collection"]["items"][0]["data"]
            data_dict = {item["name"]: item["value"] for item in data}
            team_name = data_dict.get("name", None)
            return {"team_id": team_id, "team_name": team_name}
        except (KeyError, IndexError, TypeError):
            return {"error": "Unable to retrieve team name"}

    def create_opponent(self, opponent_data: Dict[str, Any]) -> Optional[str]:
        """
        Creates an opponent for a specific team and returns their ID and name.
        """
        endpoint = "/opponents"
        response = self._post(endpoint, data=opponent_data)

        try:
            # Get the first (and only) item in the response
            item = response["collection"]["items"][0]
            data = {entry["name"]: entry["value"] for entry in item["data"]}
            opponent_id = data.get("id")
            if not opponent_id:
                logger.warning(f"Opponent ID not found in response: {response}")
            return opponent_id
        except (KeyError, IndexError, TypeError):
            logger.warning(f"Failed to parse opponent from response: {response}")

    def create_location(self, location_data: Dict[str, Any]) -> Optional[str]:
        """
        Creates a location for a specific team and returns its ID, name, and address.
        """
        endpoint = "/locations"
        response = self._post(endpoint, data=location_data)

        try:
            item = response["collection"]["items"][0]
            data = {entry["name"]: entry["value"] for entry in item["data"]}
            location_id = data.get("id")
            if not location_id:
                logger.warning(f"Location ID not found in response: {response}")
            return location_id
        except (KeyError, IndexError, TypeError):
            logger.warning(f"Failed to parse location from response: {response}")

    def create_event(self, event_data: Dict[str, Any]) -> Optional[str]:
        """
        Creates an event for a specific team and returns the event ID.
        """
        endpoint = f"/events"
        response = self._post(endpoint, data=event_data)

        try:
            data = response["collection"]["items"][0]["data"]
            data_dict = {item["name"]: item["value"] for item in data}
            event_id = data_dict.get("id")
            if not event_id:
                logger.warning(f"Event ID not found in response: {response}")
            return event_id
        except (KeyError, IndexError, TypeError):
            logger.warning(f"Failed to parse event from response: {response}")

    def get_opponents(self, team_id: str) -> Dict[str, Any]:
        """
        Fetches the list of opponents for a specific team.
        """
        response = self._get(f"/bulk_load?team_id={team_id}&types=opponent")
        if "error" in response:
            return {"error": f"Failed to fetch opponents: {response['error']}"}

        opponents = []

        for item in response.get("collection", {}).get("items", []):
            opponent_data = {d["name"]: d["value"] for d in item.get("data", [])}
            op_team_id = opponent_data.get("id")
            name = opponent_data.get("name")
            if op_team_id and name:
                opponents.append({"id": op_team_id, "name": name})

        return {"opponents": opponents}

    def get_locations(self, team_id: str) -> Dict[str, Any]:
        """
        Fetches the list of locations for a specific team.
        """
        response = self._get(f"/bulk_load?team_id={team_id}&types=location")
        if "error" in response:
            return {"error": f"Failed to fetch opponents: {response['error']}"}

        locations = []

        for item in response.get("collection", {}).get("items", []):
            data = {entry["name"]: entry["value"] for entry in item.get("data", [])}
            location_id = data.get("id")
            name = data.get("name")
            address = data.get("address")
            if location_id and name and address:
                locations.append({"id": location_id, "name": name, "address": address})

        return {"locations": locations}
