import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import io
import os
import tempfile
from report_generator import create_report

from api import EIAnalyticsAPI
from database import (
    initialize_database,
    save_measurements,
    get_database_count,
    get_measurements,
    get_all_measurements
)
# At the top of app.py
from dsp import decode_base64_float32, calculate_time_waveform, calculate_fft_metadata
#from fpdf import FPDF

UNIT_OPTIONS = {
    "G": 0,
    "mm/s²": 1,
    "mm/s": 2,
    "in/s": 3,
    "μm": 4,
    "mils": 5,
    "GE": 6
}

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Quadrant2 Vibration Dashboard",
    page_icon="📊",
    layout="wide"
)

# ============================================================
# INITIALIZE DATABASE
# ============================================================

initialize_database()

# ============================================================
# TITLE
# ============================================================

st.title("Quadrant2 Vibration Monitoring Dashboard")

st.caption(
    "EI-Analytics API based vibration monitoring system"
)


# ============================================================
# API CONNECTION
# ============================================================

EI_PASSWORD = os.getenv("EI_PASSWORD")

# Map accounts dynamically from environment variables
ACCOUNTS = {
    "Phantom": {"email": os.getenv("EI_EMAIL_PHANTOM")},
    "Wiser3X": {"email": os.getenv("EI_EMAIL_WISER3X")},
    "Defiant": {"email": os.getenv("EI_EMAIL_DEFIANT")},
}

selected_account = st.sidebar.selectbox("Account", list(ACCOUNTS.keys()))

@st.cache_resource
def get_api(email, password):
    api = EIAnalyticsAPI()
    api.login(email, password)
    return api

target_email = ACCOUNTS[selected_account]["email"]

if not target_email or not EI_PASSWORD:
    st.error(f"Missing API credentials for {selected_account}. Check your .env / Secrets.")
    st.stop()

try:
    # Authenticate with the specific selected account email
    api = get_api(target_email, EI_PASSWORD)
except Exception as e:
    st.error("Unable to connect to EI-Analytics API.")
    st.code(str(e))
    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("Machine Selection")


# ============================================================
# COMPANIES
# ============================================================

try:

    companies_response = api.get_companies()

    companies = companies_response[0]["Value"]

except Exception as e:

    st.error(f"Failed to get companies: {e}")

    st.stop()


if not companies:

    st.error("No companies were returned from EI-Analytics.")

    st.stop()


company_names = [
    company["Name"]
    for company in companies
]


# ------------------------------------------------------------
# Default to Quadrant2 if available
# ------------------------------------------------------------

company_name_list = company_names

if "Quadrant2" in company_name_list:

    default_company_index = company_name_list.index("Quadrant2")

else:

    default_company_index = 0


selected_company_name = st.sidebar.selectbox(
    "Company",
    company_name_list,
    index=default_company_index
)


selected_company = next(
    c for c in companies
    if c["Name"] == selected_company_name
)


company_id = selected_company["Id"]


# ============================================================
# AREAS
# ============================================================

try:

    areas_response = api.get_areas(company_id)

    areas = areas_response[0]["Value"]

except Exception as e:

    st.error(f"Failed to get areas: {e}")

    st.stop()


if not areas:

    st.warning(
        f"No areas were found for company '{selected_company_name}'."
    )

    st.stop()


area_names = [
    area["Name"]
    for area in areas
]


# ------------------------------------------------------------
# Default to GroundVibration if available
# ------------------------------------------------------------

if "GroundVibration" in area_names:

    default_area_index = area_names.index("GroundVibration")

else:

    default_area_index = 0


selected_area_name = st.sidebar.selectbox(
    "Area",
    area_names,
    index=default_area_index
)


selected_area = next(
    a for a in areas
    if a["Name"] == selected_area_name
)


area_id = selected_area["Id"]


# ============================================================
# MACHINES
# ============================================================

try:

    machines_response = api.get_machines(area_id)

    machines = machines_response[0]["Value"]

except Exception as e:

    st.error(f"Failed to get machines: {e}")

    st.stop()


if not machines:

    st.warning(
        f"No machines were found in area '{selected_area_name}'."
    )

    st.stop()


machine_names = [
    machine["Name"]
    for machine in machines
]


# ------------------------------------------------------------
# Default to STSB_SgSiput if available
# ------------------------------------------------------------

if "STSB_SgSiput" in machine_names:

    default_machine_index = machine_names.index("STSB_SgSiput")

else:

    default_machine_index = 0


selected_machine_name = st.sidebar.selectbox(
    "Machine",
    machine_names,
    index=default_machine_index
)


selected_machine = next(
    m for m in machines
    if m["Name"] == selected_machine_name
)


machine_code = selected_machine["Id"]


# ============================================================
# POINTS
# ============================================================

try:

    points_response = api.get_points(machine_code)

    points = points_response[0]["Value"]

except Exception as e:

    st.error(f"Failed to get points: {e}")

    st.stop()


if not points:

    st.warning(
        f"No points were found for machine '{selected_machine_name}'."
    )

    st.stop()


point_names = [
    point["Name"]
    for point in points
]


selected_point_name = st.sidebar.selectbox(
    "Point",
    point_names
)


selected_point = next(
    p for p in points
    if p["Name"] == selected_point_name
)


point_index = selected_point["Id"]


# ============================================================
# AXIS
# ============================================================

try:

    axis_response = api.get_axis(
        machine_code,
        point_index
    )

    axes = axis_response[0]["Value"]

except Exception as e:

    st.error(f"Failed to get axes: {e}")

    st.stop()


# ------------------------------------------------------------
# IMPORTANT:
# Do not invent an axis ID if the API returns nothing.
# ------------------------------------------------------------

if not axes:

    st.warning(
        "No axes were returned for this point. "
        "Please select another point."
    )

    st.stop()


axis_names = [
    axis["Name"]
    for axis in axes
]


# ------------------------------------------------------------
# Add All Axes option
# ------------------------------------------------------------

axis_options = ["All Axes (A, H, V)"] + axis_names

selected_axis_name = st.sidebar.selectbox(
    "Axis",
    axis_options,
    index=0
)

# ------------------------------------------------------------
# Determine selected axis
# ------------------------------------------------------------

if selected_axis_name == "All Axes (A, H, V)":

    selected_axis = None
    axis_id = None

    selected_axis_ids = {
        axis["Name"]: axis["Id"]
        for axis in axes
    }

else:

    selected_axis = next(
        a for a in axes
        if a["Name"] == selected_axis_name
    )

    axis_id = selected_axis["Id"]

    selected_axis_ids = {
        selected_axis_name: axis_id
    }

# ============================================================
# SELECTED ASSET INFORMATION
# ============================================================

st.subheader(
    f"{selected_machine_name} → "
    f"{selected_point_name} → "
    f"{selected_axis_name}"
)

if selected_axis_name == "All Axes (A, H, V)":

    axis_display = ", ".join(
        f"{name}: {axis_id}"
        for name, axis_id in selected_axis_ids.items()
    )

else:

    axis_display = str(axis_id)

st.write(
    f"Company: `{selected_company_name}` | "
    f"Area: `{selected_area_name}` | "
    f"Machine Code: `{machine_code}` | "
    f"Point: `{point_index}` | "
    f"Axis: `{axis_display}`"
)


# ============================================================
# DATE RANGE
# ============================================================

st.sidebar.header("Data Range")


# Use the last 30 days by default
# This gives enough data for a useful trend.

default_end_date = datetime.now().date()

default_start_date = (
    default_end_date - timedelta(days=30)
)


start_date = st.sidebar.date_input(
    "Start Date",
    default_start_date
)


end_date = st.sidebar.date_input(
    "End Date",
    default_end_date
)


# Validate date range

if start_date > end_date:

    st.error(
        "Start Date cannot be later than End Date."
    )

    st.stop()


# ============================================================
# LOAD DATA
# ============================================================

if st.button(
    "🔄 Load Vibration Data",
    type="primary"
):

    start_string = (
        f"{start_date} 00:00:00"
    )

    end_string = (
        f"{end_date} 23:59:59"
    )

    with st.spinner(
        "Retrieving EI-Analytics historical data..."
    ):

        try:

            all_records = []

            # ------------------------------------------------
            # Determine which axes to retrieve
            # ------------------------------------------------

            axes_to_load = []

            for axis_name, current_axis_id in selected_axis_ids.items():

                axes_to_load.append({
                    "name": axis_name,
                    "id": current_axis_id
                })

            # ------------------------------------------------
            # Retrieve each selected axis
            # ------------------------------------------------

            for ax in axes_to_load:

                history_response = api.get_history(
                    machine_code,
                    point_index,
                    ax["id"],
                    start_string,
                    end_string
                )

                records = history_response[0]["Value"]

                if records:

                    for record in records:

                        record_copy = record.copy()

                        # Store axis information
                        record_copy["AxisName"] = ax["name"]
                        record_copy["AxisId"] = ax["id"]

                        all_records.append(
                            record_copy
                        )

            # ------------------------------------------------
            # Check data
            # ------------------------------------------------

            if not all_records:

                st.warning(
                    "No measurements were returned "
                    "for this period."
                )

                st.stop()

            # ------------------------------------------------
            # DATAFRAME
            # ------------------------------------------------

            df = pd.DataFrame(all_records)

            # ------------------------------------------------
            # Convert date
            # ------------------------------------------------

            df["Date"] = pd.to_datetime(
                df["Date"],
                errors="coerce"
            )

            # ------------------------------------------------
            # Convert numeric columns
            # ------------------------------------------------

            numeric_columns = [
                "AccelRMS",
                "AccelSev",
                "VelRMS",
                "VelSev",
                "EnvRMS",
                "EnvSev",
                "FileId",
                "SampleRate",
                "Sensitivity",
                "Calibration",
                "Reason",
                "AxisId"
            ]

            for column in numeric_columns:

                if column in df.columns:

                    df[column] = pd.to_numeric(
                        df[column],
                        errors="coerce"
                    )

            # ------------------------------------------------
            # Sort newest → oldest
            # ------------------------------------------------

            df = df.sort_values(
                ["Date", "AxisName"],
                ascending=[False, True]
            ).reset_index(
                drop=True
            )

            # ------------------------------------------------
            # SAVE TO SQLITE
            # ------------------------------------------------

            records_saved_total = 0

            for ax in axes_to_load:

                axis_df = df[
                    df["AxisId"] == ax["id"]
                ].copy()

                if axis_df.empty:
                    continue

                records_saved = save_measurements(
                    axis_df,
                    selected_company_name,
                    selected_area_name,
                    selected_machine_name,
                    machine_code,
                    selected_point_name,
                    point_index,
                    ax["name"],
                    ax["id"]
                )

                records_saved_total += records_saved

            # ------------------------------------------------
            # SESSION STATE
            # ------------------------------------------------

            st.session_state["history"] = df

            st.session_state["history_info"] = {
                "company": selected_company_name,
                "area": selected_area_name,
                "machine": selected_machine_name,
                "machine_code": machine_code,
                "point": selected_point_name,
                "point_index": point_index,
                "axis": selected_axis_name,
                "axis_id": axis_id,
                "start_date": start_date,
                "end_date": end_date
            }

            st.success(
                f"Successfully retrieved "
                f"{len(df):,} measurements."
            )

            st.info(
                f"Added {records_saved_total:,} new "
                f"measurements to database. "
                f"Total records stored: "
                f"{get_database_count():,}"
            )

        except Exception as e:

            st.error(
                f"Failed to retrieve history data:\n{e}"
            )

# ============================================================
# DISPLAY DATA
# ============================================================

if "history" in st.session_state:

    df = st.session_state["history"]


    # ========================================================
    # ========================================================
    # DATABASE SUMMARY
    # ========================================================

    st.divider()
    st.header("📊 Measurement Summary")

    # --------------------------------------------------------
    # Make sure Date is datetime
    # --------------------------------------------------------

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Only use valid vibration measurements
    # FileId must exist and be greater than 0
    # --------------------------------------------------------

    summary_df = df[
        df["FileId"].notna()
        & (pd.to_numeric(df["FileId"], errors="coerce") > 0)
        & df["Date"].notna()
    ].copy()

    if summary_df.empty:

        st.info("No valid vibration measurements available.")

    else:

        # ----------------------------------------------------
        # ----------------------------------------------------
        # FIND LATEST VALID FILEID MEASUREMENT
        # For Acceleration RMS + Envelope
        # ----------------------------------------------------

        latest_file_date = summary_df["Date"].max()

        latest_file_df = summary_df[
            summary_df["Date"] == latest_file_date
        ].copy()

        # ----------------------------------------------------
        # FIND LATEST VELOCITY READING
        # FileId is NOT required
        # ----------------------------------------------------

        velocity_source_df = df.copy()

        velocity_source_df["VelRMS"] = pd.to_numeric(
            velocity_source_df["VelRMS"],
            errors="coerce"
        )

        velocity_source_df = velocity_source_df[
            velocity_source_df["VelRMS"] >= 0
            &
            velocity_source_df["Date"].notna()
        ]

        latest_velocity_date = velocity_source_df["Date"].max()

        latest_velocity_df = velocity_source_df[
            velocity_source_df["Date"] == latest_velocity_date
        ].copy()

        # ----------------------------------------------------
        # SELECT AXIS DATA
        # ----------------------------------------------------

        if selected_axis_name == "All Axes (A, H, V)":

            # FileId based metrics
            accel_env_axis_df = latest_file_df.copy()

            # Velocity uses latest reading
            velocity_axis_df = latest_velocity_df.copy()

        else:
            # Selected axis only
            accel_env_axis_df = latest_file_df[
                latest_file_df["AxisName"].astype(str)
                ==
                str(selected_axis_name)
            ].copy()

            velocity_axis_df = latest_velocity_df[
                latest_velocity_df["AxisName"].astype(str)
                ==
                str(selected_axis_name)
            ].copy()

        # ----------------------------------------------------
        # VALID VELOCITY
        # ----------------------------------------------------

        velocity_axis_df["VelRMS"] = pd.to_numeric(
            velocity_axis_df["VelRMS"],
            errors="coerce"
        )

        valid_velocity = velocity_axis_df[
            velocity_axis_df["VelRMS"] >= 0
        ].copy()

        # ----------------------------------------------------
        # VALID ACCELERATION
        # ----------------------------------------------------

        accel_env_axis_df["AccelRMS"] = pd.to_numeric(
            accel_env_axis_df["AccelRMS"],
            errors="coerce"
        )


        valid_acceleration = accel_env_axis_df[
            accel_env_axis_df["AccelRMS"] >= 0
        ].copy()

        # ----------------------------------------------------
        # VALID ACCELERATION ENVELOPE
        # ----------------------------------------------------

        accel_env_axis_df["EnvRMS"] = pd.to_numeric(
            accel_env_axis_df["EnvRMS"],
            errors="coerce"
        )


        valid_envelope = accel_env_axis_df[
            accel_env_axis_df["EnvRMS"] >= 0
        ].copy()

        # ----------------------------------------------------
        # GET LARGEST VALUE FOR EACH METRIC
        # ----------------------------------------------------

        velocity_row = None
        acceleration_row = None
        envelope_row = None

        if not valid_velocity.empty:

            velocity_row = valid_velocity.loc[
                valid_velocity["VelRMS"].idxmax()
            ]

        if not valid_acceleration.empty:

            acceleration_row = valid_acceleration.loc[
                valid_acceleration["AccelRMS"].idxmax()
            ]

        if not valid_envelope.empty:

            envelope_row = valid_envelope.loc[
                valid_envelope["EnvRMS"].idxmax()
            ]

        # ----------------------------------------------------
        # METRIC CARDS
        # ----------------------------------------------------

        c1, c2, c3, c4 = st.columns(4)

        # ----------------------------------------------------
        # VELOCITY RMS
        # ----------------------------------------------------

        with c1:

            if velocity_row is not None:

                velocity_value = float(
                    velocity_row["VelRMS"]
                )

                velocity_unit = str(
                    velocity_row.get(
                        "VelUnit",
                        "mm/s"
                    )
                )

                st.metric(
                    "Velocity RMS",
                    f"{velocity_value:.3f} {velocity_unit}"
                )

            else:

                st.metric(
                    "Velocity RMS",
                    "N/A"
                )

        # ----------------------------------------------------
        # ACCELERATION RMS
        # ----------------------------------------------------

        with c2:

            if acceleration_row is not None:

                acceleration_value = float(
                    acceleration_row["AccelRMS"]
                )

                acceleration_unit = str(
                    acceleration_row.get(
                        "AccelUnit",
                        "G"
                    )
                )

                st.metric(
                    "Acceleration RMS",
                    f"{acceleration_value:.4f} {acceleration_unit}"
                )

            else:

                st.metric(
                    "Acceleration RMS",
                    "N/A"
                )

        # ----------------------------------------------------
        # ACCELERATION ENVELOPE
        # ----------------------------------------------------

        with c3:

            if envelope_row is not None:

                envelope_value = float(
                    envelope_row["EnvRMS"]
                )

                envelope_unit = str(
                    envelope_row.get(
                        "EnvUnit",
                        "gE"
                    )
                )

                st.metric(
                    "Acceleration Envelope",
                    f"{envelope_value:.5f} {envelope_unit}"
                )

            else:

                st.metric(
                    "Acceleration Envelope",
                    "N/A"
                )

        # ----------------------------------------------------
        # TOTAL MEASUREMENTS
        # ----------------------------------------------------

        with c4:

            st.metric(
                "Measurements",
                f"{len(df):,}"
            )

        # ----------------------------------------------------
        # SUMMARY INFORMATION
        # ----------------------------------------------------

        if selected_axis_name == "All Axes (A, H, V)":

            display_date = max(
                latest_file_date,
                latest_velocity_date
            )

        else:

            display_date = max(
                latest_file_date,
                latest_velocity_date
            )


        st.caption(
            f"Latest valid measurement: "
            f"{display_date.strftime('%Y-%m-%d %H:%M:%S')} "
            f"| Axis selection: {selected_axis_name}"
        )

        st.session_state["report_summary"] = {
            "Acceleration RMS":
            acceleration_row["AccelRMS"]
            if acceleration_row is not None
            else "N/A",

            "Velocity RMS":
            velocity_row["VelRMS"]
            if velocity_row is not None
            else "N/A",

            "Acceleration Envelope":
            envelope_row["EnvRMS"]
            if envelope_row is not None
            else "N/A"

        }

    # ========================================================
    # DATA INFORMATION
    # ========================================================

    if "history_info" in st.session_state:

        info = st.session_state["history_info"]


        st.caption(
            f"Data range: "
            f"{info['start_date']} → "
            f"{info['end_date']} "
            f"| Machine Code: {info['machine_code']} "
            f"| Point: {info['point_index']} "
            f"| Axis: {info['axis']}"
        )


    #
    # ========================================================
    # VELOCITY RMS TREND
    # ========================================================

    st.divider()

    st.header("📈 Velocity RMS Trend")


    velocity_df = df[
        df["VelRMS"] >= 0
    ].copy()


    if not velocity_df.empty:

        fig_velocity = go.Figure()


        fig_velocity.add_trace(
            go.Scatter(
                x=velocity_df["Date"],
                y=velocity_df["VelRMS"],
                mode="lines",
                name="Velocity RMS",
                hovertemplate=(
                    "Time: %{x}<br>"
                    "Velocity RMS: %{y:.3f} mm/s"
                    "<extra></extra>"
                )
            )
        )


        fig_velocity.update_layout(
            xaxis_title="Time",
            yaxis_title="Velocity RMS (mm/s)",
            hovermode="x unified",
            height=450
        )


        st.plotly_chart(
            fig_velocity,
            width="stretch"
        )


    else:

        st.info(
            "No valid velocity RMS values were found."
        )


    # ========================================================
    # ACCELERATION RMS TREND
    # ========================================================

    st.header("📈 Acceleration RMS Trend")


    acceleration_df = df[
        df["AccelRMS"] >= 0
    ].copy()


    if not acceleration_df.empty:

        fig_acceleration = go.Figure()


        fig_acceleration.add_trace(
            go.Scatter(
                x=acceleration_df["Date"],
                y=acceleration_df["AccelRMS"],
                mode="lines",
                name="Acceleration RMS",
                hovertemplate=(
                    "Time: %{x}<br>"
                    "Acceleration RMS: %{y:.5f}"
                    "<extra></extra>"
                )
            )
        )


        fig_acceleration.update_layout(
            xaxis_title="Time",
            yaxis_title="Acceleration RMS",
            hovermode="x unified",
            height=450
        )


        st.plotly_chart(
            fig_acceleration,
            width="stretch"
        )


    else:

        st.info(
            "No valid acceleration RMS values were found "
            "for this dataset."
        )

    
    # ========================================================
    # HISTORICAL DATABASE
    # ========================================================

    #st.divider()


    st.header("🗄 Historical Measurement Database")

    st.write(
        "The table below contains historical measurements stored "
        "in the local SQLite database."
    )


    # ------------------------------------------------------------
    # DATABASE DATE RANGE
    # ------------------------------------------------------------

    database_start = st.date_input(
        "Database Start Date",
        value=start_date,
        key="database_start"
    )

    database_end = st.date_input(
        "Database End Date",
        value=end_date,
        key="database_end"
    )


    # ------------------------------------------------------------
    # LOAD DATA DIRECTLY FROM SQLITE
    # ------------------------------------------------------------

    database_df = get_measurements(
        machine_code=machine_code,
        point_index=point_index,
        axis_id=axis_id
    )


    # ------------------------------------------------------------
    # CHECK DATABASE DATA
    # ------------------------------------------------------------

    if database_df.empty:

        st.info(
            "No historical measurements are stored in the database "
            "for the selected machine, point and axis."
        )

    else:

        # --------------------------------------------------------
        # RENAME SQLITE COLUMNS TO MATCH API FORMAT
        # --------------------------------------------------------

        database_df = database_df.rename(
            columns={
                "date": "Date",
                "file_id": "FileId",
                "reason": "Reason",
                "axis": "Axis",

                "sample_rate": "SampleRate",
                "sensitivity": "Sensitivity",
                "calibration": "Calibration",

                "accel_rms": "AccelRMS",
                "accel_unit": "AccelUnit",
                "accel_sev": "AccelSev",

                "vel_rms": "VelRMS",
                "vel_unit": "VelUnit",
                "vel_sev": "VelSev",

                "env_rms": "EnvRMS",
                "env_unit": "EnvUnit",
                "env_sev": "EnvSev"
            }
        )


        # --------------------------------------------------------
        # CONVERT DATE
        # --------------------------------------------------------

        database_df["Date"] = pd.to_datetime(
            database_df["Date"],
            errors="coerce"
        )


        # --------------------------------------------------------
        # DATE FILTER
        # --------------------------------------------------------

        filtered_df = database_df[
            (database_df["Date"].dt.date >= database_start)
            &
            (database_df["Date"].dt.date <= database_end)
        ].copy()


        # ------------------------------------------------------------
        # HISTORICAL FILTERS
        # ------------------------------------------------------------

        st.subheader("🔎 Historical Filters")

        filter_col1, filter_col2, filter_col3 = st.columns(3)

        with filter_col1:
            filter_start = st.date_input(
                "From Date",
                value=database_start,
                key="history_filter_start"
            )

        with filter_col2:
            filter_end = st.date_input(
                "To Date",
                value=database_end,
                key="history_filter_end"
            )

        with filter_col3:
            selected_history_axis = st.selectbox(
                "Axis",
                ["All Axes", "A", "H", "V"],
                key="history_axis_filter"
            )

        filter_col4, filter_col5 = st.columns(2)

        with filter_col4:
            file_id_filter = st.text_input(
                "File ID",
                placeholder="Example: 16678",
                key="history_file_filter"
            )       

        with filter_col5:

            reason_options = ["All"]

            if "Reason" in database_df.columns:
                reasons = (
                    database_df["Reason"]
                    .dropna()
                    .astype(str)
                    .unique()
                    .tolist()
                )

                reason_options += sorted(reasons)

            selected_reason = st.selectbox(
                "Reason",
                reason_options,
                key="history_reason_filter"
            )

        # ------------------------------------------------------------
        # General search
        # ------------------------------------------------------------

        search_term = st.text_input(
            "🔎 Search",
            placeholder=(
                "Search date, FileId, "
                "RMS values, etc."
            ),
            key="history_search"
        )
        # ------------------------------------------------------------
        # APPLY FILTERS
        # ------------------------------------------------------------

        filtered_df = database_df.copy()

        # Date
        filtered_df = filtered_df[
            (filtered_df["Date"].dt.date >= filter_start)
            &
            (filtered_df["Date"].dt.date <= filter_end)
        ]

        # Axis
        if selected_history_axis != "All Axes":

            if "Axis" in filtered_df.columns:

                filtered_df = filtered_df[
                    filtered_df["Axis"]
                    .astype(str)
                    .str.strip()
                    .str.upper()
                    == selected_history_axis.upper()
                ]

            elif "AxisName" in filtered_df.columns:

                filtered_df = filtered_df[
                    filtered_df["AxisName"].astype(str).str.upper()
                    == selected_history_axis.upper()
                ]

        # File ID
        if file_id_filter.strip():

            filtered_df = filtered_df[
                filtered_df["FileId"]
                .astype(str)
                .str.contains(
                    file_id_filter.strip(),
                    case=False,
                    na=False
                )
            ]

        # Reason
        if selected_reason != "All":

            filtered_df = filtered_df[
                filtered_df["Reason"].astype(str)
                == selected_reason
            ]

        # General search
        if search_term.strip():

            search_mask = filtered_df.astype(str).apply(
                lambda column: column.str.contains(
                    search_term.strip(),
                    case=False,
                    na=False
                )
            ).any(axis=1)

            filtered_df = filtered_df[
                search_mask
            ]

        filtered_df = filtered_df.sort_values(
            ["Date", "Axis"],
            ascending=[False, True]
        ).reset_index(drop=True)

        # --------------------------------------------------------
        # DISPLAY COLUMNS
        # --------------------------------------------------------

        display_columns = [
            "Date",
            "FileId",
            "Axis",
            "AccelRMS",
            "AccelUnit",
            "AccelSev",
            "VelRMS",
            "VelUnit",
            "VelSev",
            "EnvRMS",
            "EnvUnit",
            "EnvSev",
            "SampleRate",
            "Reason"
        ]


        # Only use columns that actually exist
        display_columns = [
            column
            for column in display_columns
            if column in filtered_df.columns
        ]


        display_df = filtered_df[display_columns].copy()


        # --------------------------------------------------------
        # REPLACE -1 WITH BLANK FOR DISPLAY
        # --------------------------------------------------------

        display_df = display_df.replace(
            -1,
            pd.NA
        )


        # --------------------------------------------------------
        # DATABASE SUMMARY
        # --------------------------------------------------------

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Database Records",
                f"{len(database_df):,}"
            )

        with col2:
            st.metric(
                "Records in Date Range",
                f"{len(filtered_df):,}"
            )

        with col3:
            st.metric(
                "Records Displayed",
            f"{len(display_df):,}"
            )


        # --------------------------------------------------------
        # TABLE
        # --------------------------------------------------------

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )


        # --------------------------------------------------------
        # CSV DOWNLOAD
        # --------------------------------------------------------

        csv = filtered_df.to_csv(
            index=False
        ).encode("utf-8")


        st.download_button(
            label="⬇️ Download Historical Data (CSV)",
            data=csv,
            file_name="ei_historical_measurements.csv",
            mime="text/csv"
        )


        # --------------------------------------------------------
        # DATA QUALITY
        # --------------------------------------------------------

        st.subheader("📊 Data Quality")

        valid_velocity = (
            filtered_df["VelRMS"] >= 0
        ).sum() if "VelRMS" in filtered_df.columns else 0

        valid_acceleration = (
            filtered_df["AccelRMS"] >= 0
        ).sum() if "AccelRMS" in filtered_df.columns else 0

        valid_envelope = (
            filtered_df["EnvRMS"] >= 0
        ).sum() if "EnvRMS" in filtered_df.columns else 0


        q1, q2, q3, q4 = st.columns(4)

        with q1:
            st.metric(
                "Total",
                f"{len(filtered_df):,}"
            )

        with q2:
            st.metric(
                "Valid Velocity",
                f"{valid_velocity:,}"
            )

        with q3:
            st.metric(
                "Valid Acceleration",
                f"{valid_acceleration:,}"
            )

        with q4:
            st.metric(
                "Valid Envelope",
                f"{valid_envelope:,}"
            )

    # =========================================================
    # SPECTRAL & TIME WAVEFORM ANALYSIS SECTION
    # =========================================================

    st.divider()
    st.header("🔬 Spectral & Time Waveform Analysis")

    # 1. Filter valid measurement files
    valid_files_df = df[df["FileId"].notna() & (df["FileId"] > 0)].copy()

    if valid_files_df.empty:
        st.warning("No valid vibration measurements available for analysis.")
    else:
        # 2. Controls & Variable Definitions
        col_sel = st.columns(1)[0]

        with col_sel:

            selected_index = st.selectbox(
                "Select Measurement File",
                valid_files_df.index,
                format_func=lambda i: (
                    f"FileId {int(valid_files_df.loc[i, 'FileId'])} | "
                    f"Date: {valid_files_df.loc[i, 'Date']}"
                )
            )

        selected_row = valid_files_df.loc[selected_index]

        file_id = int(
            selected_row["FileId"]
        )

        # =========================================================
        # SIGNAL FETCHING & DYNAMIC ANALYSIS
        # =========================================================

        if st.button("📈 Fetch Signal Data", type="primary"):
            with st.spinner("Retrieving TWF and FFT data from EI-Analytics..."):
                try:
                    # ---------------------------------------------------------
                    # Determine axes for signal analysis
                    # ---------------------------------------------------------

                    axes_to_fetch = []

                    for axis_name, current_axis_id in selected_axis_ids.items():

                        if axis_name.upper().startswith("A"):
                            color = "#F7AF33" #"#2E8B57"

                        elif axis_name.upper().startswith("H"):
                            color = "#00C337" #"#6DC0FA"

                        elif axis_name.upper().startswith("V"):
                            color = "#56B9FF" #"#82FFC1"

                        else:
                            color = "#7F7F7F"

                        axes_to_fetch.append({
                            "name": axis_name,
                            "id": current_axis_id,
                            "color": color
                        })

                    fetched_data = {}

                    for ax in axes_to_fetch:
                        # 1. Fetch FFT Spectrum (OutputType=1, SignalTypeOut=2 -> mm/s)
                        fft_resp = api.get_fft_base64(
                            machine_code=machine_code,
                            point_index=point_index,
                            axis=ax["id"],
                            file_id=file_id,
                            output_type=1,
                            signal_type=fft_signal_type,
                            hz=False
                        )

                        # 2. Fetch Time Waveform (OutputType=2, SignalTypeOut=2 -> mm/s)
                        twf_resp = api.get_fft_base64(
                            machine_code=machine_code,
                            point_index=point_index,
                            axis=ax["id"],
                            file_id=file_id,
                            output_type=2,
                            signal_type=twf_signal_type,
                            hz=False
                        )

                        if fft_resp and twf_resp:
                            val_fft = fft_resp[0].get("Value", {})
                            val_twf = twf_resp[0].get("Value", {})

                            sr_fft = float(val_fft.get("SR", 0))
                            sr_twf = float(val_twf.get("SR", 0))

                            fft_signal = decode_base64_float32(val_fft.get("base64", ""))
                            twf_signal = decode_base64_float32(val_twf.get("base64", ""))

                            # Frequency Axis Construction (Jupyter-verified)
                            num_bins = len(fft_signal)
                            n_fft = num_bins * 2
                            df_step = sr_fft / n_fft if n_fft > 0 else 0
                            freq_axis = np.arange(num_bins) * df_step

                            # Time Axis Construction
                            twf_points = len(twf_signal)
                            time_axis = np.arange(twf_points) / sr_twf if sr_twf > 0 else np.array([])

                            fetched_data[ax["name"]] = {
                                "fft_signal": fft_signal,
                                "freq_axis": freq_axis,
                                "twf_signal": twf_signal,
                                "time_axis": time_axis,
                                "sr_fft": sr_fft,
                                "sr_twf": sr_twf,
                                "twf_points": twf_points,
                                "color": ax["color"]
                            }

                    st.session_state["fetched_data"] = fetched_data
                    st.session_state["active_file_id"] = file_id
                    st.session_state["active_row"] = selected_row
                    st.success("TWF and FFT data retrieved successfully!")

                except Exception as e:
                    st.error(f"Failed to fetch signal data: {e}")

        # =========================================================
        # RENDERING PLOTS & METADATA OVERLAYS
        # =========================================================

        if "fetched_data" in st.session_state and st.session_state.get("active_file_id") == file_id:
            data_dict = st.session_state["fetched_data"]
            active_row = st.session_state["active_row"]
            rec_date = pd.to_datetime(active_row["Date"]).strftime("%Y/%m/%d")

            #tab_fft, tab_twf = st.tabs(["📊 FFT Spectrum", "🌊 Time Waveform (TWF)"])

        # ---------------------------------------------------------
        # TIME WAVEFORM (TWF)
        # ---------------------------------------------------------
            st.subheader("🌊 Time Waveform (TWF)")
            twf_unit = st.selectbox(
                "TWF Unit",
                list(UNIT_OPTIONS.keys()),
                index=0,
                key="twf_unit"
            )
            twf_signal_type = UNIT_OPTIONS[twf_unit]

            fig_twf = go.Figure()
            first_entry = next(iter(data_dict.values()))
            sr_twf = first_entry["sr_twf"]
            twf_vals = first_entry["twf_signal"]
            twf_points = first_entry["twf_points"]

            # 1. Compute RMS directly from downloaded time series array: sqrt(mean(TWF^2))
            if len(twf_vals) > 0:
                twf_rms = np.sqrt(np.mean(twf_vals ** 2))
                twf_rms_str = f"{twf_rms:.4f}"
            else:
                twf_rms_str = "N/A"

            # 2. Compute exact duration: total samples / sampling rate
            rec_time = (twf_points / sr_twf) if sr_twf > 0 else 0.0

            for axis_label, s in data_dict.items():
                fig_twf.add_trace(
                    go.Scatter(
                        x=s["time_axis"],
                        y=s["twf_signal"],
                        mode="lines",
                        name=axis_label,
                        line=dict(color=s["color"], width=1.0)
                    )
                )

            twf_metadata_lines = [
                f"<b>Date: {rec_date}</b>",
                f" RMS: {twf_rms_str} ",
                "---",
                f" SR: {int(round(sr_twf))}",
                f" Rec: {rec_time:.1f} S"
            ]

            fig_twf.add_annotation(
                xref="paper", yref="paper",
                x=0.98, y=0.98,
                text="<br>".join(twf_metadata_lines),
                showarrow=False, align="left",
                bordercolor="#cccccc", borderwidth=1, borderpad=8,
                bgcolor="#ffffff", opacity=0.9,
                font=dict(size=11, family="monospace", color="black")
            )

            fig_twf.update_layout(
                title=f"<b>{selected_machine_name} - {selected_point_name} - {selected_axis_name} TWF</b>",
                xaxis_title="Time (s)", yaxis_title=twf_unit,
                height=500, template="plotly_white",
                xaxis=dict(showgrid=True, gridcolor="#e5e5e5", rangeslider=dict(visible=True)),
                yaxis=dict(showgrid=True, gridcolor="#e5e5e5")
            )
            st.plotly_chart(fig_twf, use_container_width=True) 

            # ---------------------------------------------------------
            # FFT SPECTRUM
            # ---------------------------------------------------------
            st.subheader("📊 FFT Spectrum")
            fft_unit = st.selectbox(
                "FFT Unit",
                list(UNIT_OPTIONS.keys()),
                index=2,
                key="fft_unit"
            )
            fft_signal_type = UNIT_OPTIONS[fft_unit]

            fig_fft = go.Figure()
            first_entry = next(iter(data_dict.values()))
            sr_fft = first_entry["sr_fft"]
            fft_vals = first_entry["fft_signal"]
            num_bins = len(fft_vals)

            for axis_label, s in data_dict.items():
                fig_fft.add_trace(
                    go.Scatter(
                        x=s["freq_axis"],
                        y=s["fft_signal"],
                        mode="lines",
                        name=axis_label,
                        line=dict(color=s["color"], width=1.2)
                    )
                )
            # 80% usable lines factor
            lr_val = int(num_bins * 0.78125) if num_bins > 0 else 12800
            fr_val = int(round((num_bins * (sr_fft / (num_bins * 2))))) if sr_fft > 0 else 0

            # Calculated DIRECTLY from FFT payload array
            max_val = np.max(fft_vals) if num_bins > 0 else 0.0

            rpm_raw = active_row.get("RPM", None)
            rpm_str = f"{float(rpm_raw):.0f}" if pd.notna(rpm_raw) and rpm_raw is not None else "N/A"

            fft_metadata_lines = [                    f"<b>Date: {rec_date}</b>",
                f"Max = {max_val:.6f} mm/s",
                f"RPM: {rpm_str}",
                "---",
                f"LR: {lr_val}",
                f"FR: {fr_val}",
                f"SR: {int(round(sr_fft))}"
            ]

            fig_fft.add_annotation(
                xref="paper", yref="paper",
                x=0.98, y=0.98,
                text="<br>".join(fft_metadata_lines),
                showarrow=False, align="left",
                bordercolor="#cccccc", borderwidth=1, borderpad=8,
                bgcolor="#ffffff", opacity=0.9,
                font=dict(size=11, family="monospace", color="black")
            )

            fig_fft.update_layout(
                title=f"<b>{selected_machine_name} - {selected_point_name} - {selected_axis_name} FFT</b>",
                xaxis_title="Hz", yaxis_title=fft_unit,
                height=500, template="plotly_white",
                xaxis=dict(showgrid=True, gridcolor="#e5e5e5", rangeslider=dict(visible=True)),
                yaxis=dict(showgrid=True, gridcolor="#e5e5e5")
            )
            st.plotly_chart(fig_fft, use_container_width=True)

    #
    st.divider()

    st.header("📄 Report")
    if st.button(
        "Generate Quick Report"
    ):

        filename = (
            "Quadrant2_Vibration_Report.pdf"
        )

        create_report(
            filename,

            {

            "Machine":
            selected_machine_name,

            "Point":
            selected_point_name,

            "Axis":
            selected_axis_name,

            "Date Range":
            f"{start_date} - {end_date}",

            "File ID":
            file_id

            },

            st.session_state.get(
                "report_summary",
                {}
            )

        )

        with open(
            filename,
            "rb"
        ) as pdf:

            st.download_button(

                "Download Report",
                pdf,
                filename,
                "application/pdf"
            )