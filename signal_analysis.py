import streamlit as st
import numpy as np
import plotly.graph_objects as go


UNIT_OPTIONS = {

    "G":0,
    "mm/s²":1,
    "mm/s":2,
    "in/s":3,
    "μm":4,
    "mils":5,
    "GE":6

}


def show_signal_analysis(
        api,
        machine_code,
        point_index,
        axis_id,
        file_id,
        selected_machine_name,
        selected_point_name,
        selected_axis_name
):