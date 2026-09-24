from api import EIAnalyticsAPI


api = EIAnalyticsAPI()


print("====================================")
print("EI-ANALYTICS API TEST")
print("====================================")


# ============================================================
# 1. LOGIN
# ============================================================

print("\n[1] Logging in...")

api.login()

print("Login successful.")
print("Token received.")


# ============================================================
# 2. COMPANIES
# ============================================================

print("\n[2] Getting companies...")

companies_response = api.get_companies()

companies = companies_response[0]["Value"]

for company in companies:
    print(
        f"Company: {company['Name']} "
        f"(ID: {company['Id']})"
    )


# Select first company
selected_company = next(
    company
    for company in companies
    if company["Name"] == "Quadrant2"
)

company_id = selected_company["Id"]

print(
    f"\nSelected company: {selected_company['Name']}"
)

print(
    f"Company ID: {company_id}"
)


# ============================================================
# 3. AREAS
# ============================================================

print("\n[3] Getting areas...")

areas_response = api.get_areas(company_id)

areas = areas_response[0]["Value"]

for area in areas:
    print(
        f"Area: {area['Name']} "
        f"(ID: {area['Id']})"
    )


# Select first area
selected_area = areas[0]

area_id = selected_area["Id"]

print(
    f"\nSelected area: "
    f"{selected_area['Name']}"
)

print(
    f"Area ID: {area_id}"
)


# ============================================================
# 4. MACHINES
# ============================================================

print("\n[4] Getting machines...")

machines_response = api.get_machines(area_id)

machines = machines_response[0]["Value"]

for machine in machines:
    print(
        f"Machine: {machine['Name']} "
        f"(Code: {machine['Id']})"
    )


# Select first machine
selected_machine = machines[0]

machine_code = selected_machine["Id"]

print(
    f"\nSelected machine: "
    f"{selected_machine['Name']}"
)

print(
    f"Machine code: {machine_code}"
)


# ============================================================
# 5. POINTS
# ============================================================

print("\n[5] Getting points...")

points_response = api.get_points(machine_code)

print("\nRaw Points Response:")
print(points_response)

points = points_response[0]["Value"]

for point in points:
    print(
        f"Point: {point['Name']} "
        f"(ID: {point['Id']})"
    )


# Select first point
selected_point = points[0]

point_index = selected_point["Id"]

print(
    f"\nSelected point: "
    f"{selected_point['Name']}"
)

print(
    f"Point index: {point_index}"
)


# ============================================================
# 6. AXIS
# ============================================================

print("\n[6] Getting axis...")

axis_response = api.get_axis(
    machine_code,
    point_index
)

print("\nRaw Axis Response:")
print(axis_response)

axes = axis_response[0]["Value"]

# Handle empty axis list safely
if not axes:
    print(
        "\n⚠️ No axes returned for this point."
    )

    axis_id = None

else:

    selected_axis = axes[0]

    axis_id = selected_axis["Id"]

    print(
        f"\nSelected axis: "
        f"{selected_axis['Name']}"
    )

    print(
        f"Axis ID: {axis_id}"
    )


# ============================================================
# 7. HISTORY MEASURES
# ============================================================

if axis_id is not None:

    print("\n[7] Getting history measures...")

    history_response = api.get_history(
        machine_code=machine_code,
        point_index=point_index,
        axis=axis_id,
        start_date="2026-09-15 00:00:00", # 1/8/2026
        end_date="2026-09-21 21:59:59" # 21/9/2026
    )

    print("\nRaw History Response:")
    print(history_response)

else:

    print(
        "\n[7] Skipping history because "
        "no axis was returned."
    )

# ============================================================
# 8. DISPLAY HISTORY
# ============================================================

try:

    history = history_response[0]["Value"]

    print(
        f"\nNumber of measurements: "
        f"{len(history)}"
    )

    for measurement in history[:10]:

        print(
            "\n--------------------------------"
        )

        print(
            f"Date: {measurement.get('Date')}"
        )

        print(
            f"File ID: "
            f"{measurement.get('FileId')}"
        )

        print(
            f"Acceleration RMS: "
            f"{measurement.get('AccelRMS')} "
            f"{measurement.get('AccelUnit')}"
        )

        print(
            f"Velocity RMS: "
            f"{measurement.get('VelRMS')} "
            f"{measurement.get('VelUnit')}"
        )

        print(
            f"Envelope RMS: "
            f"{measurement.get('EnvRMS')} "
            f"{measurement.get('EnvUnit')}"
        )

        print(
            f"Acceleration Severity: "
            f"{measurement.get('AccelSev')}"
        )

        print(
            f"Velocity Severity: "
            f"{measurement.get('VelSev')}"
        )

        print(
            f"Envelope Severity: "
            f"{measurement.get('EnvSev')}"
        )

except Exception as e:

    print(
        "\nCould not process history response:"
    )

    print(e)


print("\n====================================")
print("API TEST COMPLETE")
print("====================================")