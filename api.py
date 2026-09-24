import os
import base64
import requests
import numpy as np

from dotenv import load_dotenv


load_dotenv()


BASE_URL = "https://api.eianalytic.com/ApiWeb.svc"

EMAIL = os.getenv("EI_EMAIL")
PASSWORD = os.getenv("EI_PASSWORD")


class EIAnalyticsAPI:

    def __init__(self):
        self.token = None

    # ---------------------------------------------------------
    # Generic POST function
    # ---------------------------------------------------------
    def post(self, endpoint, payload):
        url = f"{BASE_URL}/{endpoint}"

        response = requests.post(
            url,
            json=payload,
            timeout=30
        )

        response.raise_for_status()

        return response.json()

    # ---------------------------------------------------------
    # LOGIN
    # ---------------------------------------------------------
    def login(self, email, password):

        payload = {

            "email": email,

            "password": password

        }


        data = self.post(
            "Login",
            payload
        )


        try:

            self.token = data[0]["Value"][0]["Token"]

        except Exception as e:

            raise Exception(
                f"Login failed\n{data}"
            ) from e


        return data

    # ---------------------------------------------------------
    # COMPANIES
    # ---------------------------------------------------------
    def get_companies(self):

        payload = {
            "Token": self.token
        }

        return self.post("GetCompanies", payload)

    # ---------------------------------------------------------
    # AREAS
    # ---------------------------------------------------------
    def get_areas(self, company_id):

        payload = {
            "idcompany": company_id,
            "Token": self.token
        }

        return self.post("GetAreas", payload)

    # ---------------------------------------------------------
    # MACHINES
    # ---------------------------------------------------------
    def get_machines(self, area_id):

        payload = {
            "idarea": area_id,
            "Token": self.token
        }

        return self.post("GetMachines", payload)

    # ---------------------------------------------------------
    # POINTS
    # ---------------------------------------------------------
    def get_points(self, machine_code):

        payload = {
            "machinecode": machine_code,
            "Token": self.token
        }

        return self.post("GetPoints", payload)

    # ---------------------------------------------------------
    # AXIS
    # ---------------------------------------------------------
    def get_axis(self, machine_code, point_index):

        payload = {
            "pointindex": point_index,
            "machinecode": machine_code,
            "Token": self.token
        }

        return self.post("GetAxis", payload)

    # ---------------------------------------------------------
    # HISTORY MEASURES
    # ---------------------------------------------------------
    def get_history(
        self,
        machine_code,
        point_index,
        axis,
        start_date,
        end_date
    ):

        payload = {
            "machinecode": machine_code,
            "pointindex": point_index,
            "axis": axis,
            "StartDate": start_date,
            "EndDate": end_date,
            "getRMS": True,
            "Token": self.token
        }

        return self.post("GetHistoryMeasures", payload)

    # ---------------------------------------------------------
    # FFT / TWF BASE64
    # ---------------------------------------------------------
    def get_fft_base64(
        self,
        machine_code,
        point_index,
        axis,
        file_id,
        output_type=1,
        signal_type=2,
        hz=False
    ):

        payload = {
            "OutputType": output_type,
            "SignalTypeOut": signal_type,
            "axis": True,
            "fileid": file_id,
            "hz": hz,
            "machinecode": machine_code,
            "pointindex": point_index,
            "Token": self.token
        }

        # Use the same POST method as the other API functions
        return self.post("GetFFT_Base64", payload)

    # ---------------------------------------------------------
    # Decode EI Base64 Float32 data
    # ---------------------------------------------------------
    @staticmethod
    def decode_base64_float32(base64_string):

        raw_bytes = base64.b64decode(base64_string)

        values = np.frombuffer(
            raw_bytes,
            dtype=np.float32
        )

        return values
    
    def get_extra_values(self, machine_code, point_index, unit_id=20, start_date="2020-01-01", end_date="2026-12-31"):
        """Fetches extra sensor metrics such as Temperature (Unit ID 20)."""
        url = f"{self.base_url}/GetExtraValues"
        payload = {
            "Token": self.token,
            "machinecode": int(machine_code),
            "pointindex": int(point_index),
            "unit": int(unit_id),
            "StartDate": start_date,
            "EndDate": end_date
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0 and "Value" in data[0]:
                    return data[0]["Value"]
        except Exception as e:
            print(f"Error fetching extra values: {e}")
        return []