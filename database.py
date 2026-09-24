import sqlite3
import pandas as pd
from pathlib import Path


# ============================================================
# DATABASE LOCATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(
    exist_ok=True
)

DATABASE_PATH = DATA_DIR / "ei_data.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    conn = sqlite3.connect(
        DATABASE_PATH,
        check_same_thread=False
    )

    return conn


# ============================================================
# CREATE DATABASE TABLE
# ============================================================

def initialize_database():

    conn = get_connection()

    cursor = conn.cursor()


    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS measurements (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            company TEXT,

            area TEXT,

            machine TEXT,

            machine_code INTEGER,

            point TEXT,

            point_index INTEGER,

            axis TEXT,

            axis_id INTEGER,

            date TEXT,

            file_id INTEGER,

            reason INTEGER,

            sample_rate REAL,

            sensitivity REAL,

            calibration REAL,

            accel_rms REAL,

            accel_unit TEXT,

            accel_sev REAL,

            vel_rms REAL,

            vel_unit TEXT,

            vel_sev REAL,

            env_rms REAL,

            env_unit TEXT,

            env_sev REAL,

            UNIQUE(
                machine_code,
                point_index,
                axis_id,
                date,
                file_id
            )
        )
        """
    )


    conn.commit()

    conn.close()


# ============================================================
# SAVE DATAFRAME
# ============================================================

def save_measurements(
    df,
    company,
    area,
    machine,
    machine_code,
    point,
    point_index,
    axis,
    axis_id
):

    if df.empty:

        return 0


    conn = get_connection()


    records_saved = 0


    for _, row in df.iterrows():

        try:

            conn.execute(
                """
                INSERT OR IGNORE INTO measurements (

                    company,
                    area,
                    machine,
                    machine_code,
                    point,
                    point_index,
                    axis,
                    axis_id,

                    date,
                    file_id,
                    reason,

                    sample_rate,
                    sensitivity,
                    calibration,

                    accel_rms,
                    accel_unit,
                    accel_sev,

                    vel_rms,
                    vel_unit,
                    vel_sev,

                    env_rms,
                    env_unit,
                    env_sev

                )

                VALUES (

                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,

                    ?,
                    ?,
                    ?,

                    ?,
                    ?,
                    ?,

                    ?,
                    ?,
                    ?,

                    ?,
                    ?,
                    ?,

                    ?,
                    ?,
                    ?

                )
                """,

                (

                    company,
                    area,
                    machine,
                    machine_code,
                    point,
                    point_index,
                    axis,
                    axis_id,

                    str(row.get("Date", "")),
                    row.get("FileId"),
                    row.get("Reason"),

                    row.get("SampleRate"),
                    row.get("Sensitivity"),
                    row.get("Calibration"),

                    row.get("AccelRMS"),
                    row.get("AccelUnit"),
                    row.get("AccelSev"),

                    row.get("VelRMS"),
                    row.get("VelUnit"),
                    row.get("VelSev"),

                    row.get("EnvRMS"),
                    row.get("EnvUnit"),
                    row.get("EnvSev")

                )
            )


            if conn.execute(
                "SELECT changes()"
            ).fetchone()[0] > 0:

                records_saved += 1


        except Exception as e:

            print(
                f"Database insert error: {e}"
            )


    conn.commit()

    conn.close()


    return records_saved


# ============================================================
# GET ALL MEASUREMENTS
# ============================================================

def get_all_measurements():

    conn = get_connection()


    df = pd.read_sql_query(
        """
        SELECT *

        FROM measurements

        ORDER BY datetime(date) DESC
        """,

        conn
    )


    conn.close()


    return df


# ============================================================
# GET MEASUREMENTS FOR SPECIFIC ASSET
# ============================================================

def get_measurements(
    machine_code=None,
    point_index=None,
    axis_id=None
):

    conn = get_connection()


    query = """
        SELECT *

        FROM measurements

        WHERE 1=1
    """


    parameters = []


    if machine_code is not None:

        query += """
            AND machine_code = ?
        """

        parameters.append(
            machine_code
        )


    if point_index is not None:

        query += """
            AND point_index = ?
        """

        parameters.append(
            point_index
        )


    if axis_id is not None:

        query += """
            AND axis_id = ?
        """

        parameters.append(
            axis_id
        )


    query += """
        ORDER BY datetime(date) ASC
    """


    df = pd.read_sql_query(
        query,
        conn,
        params=parameters
    )


    conn.close()


    return df


# ============================================================
# DATABASE STATISTICS
# ============================================================

def get_database_count():

    conn = get_connection()


    result = conn.execute(
        """
        SELECT COUNT(*)
        FROM measurements
        """
    ).fetchone()


    conn.close()


    return result[0]


# ============================================================
# CLEAR DATABASE
# ============================================================

def clear_database():

    conn = get_connection()


    conn.execute(
        """
        DELETE FROM measurements
        """
    )


    conn.commit()

    conn.close()