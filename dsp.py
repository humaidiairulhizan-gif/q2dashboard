import base64
import numpy as np

def decode_base64_float32(base64_string):
    """
    Decode Base64 vibration data returned by EI-Analytics
    into a NumPy float32 array.
    """
    raw_bytes = base64.b64decode(base64_string)
    return np.frombuffer(raw_bytes, dtype=np.float32)

def calculate_time_waveform(signal, sample_rate):
    """
    Generates time vector (in seconds/ms) and amplitude for Time Waveform (TWF).
    """
    signal = np.asarray(signal, dtype=float)
    n = len(signal)
    if n == 0 or sample_rate <= 0:
        return np.array([]), np.array([])
    
    # Time array in milliseconds (standard EI representation)
    time_ms = (np.arange(n) / sample_rate) * 1000.0
    return time_ms, signal

def calculate_fft_metadata(sample_rate, fft_points, rpm=1307):
    """
    Calculates technical parameters shown on EI-Analytic FFT sidebar overlay:
    - Resolution (Res = SR / (2 * fft_points) or SR / Lines)
    - Frequency Range (FR = SR / 2)
    - Lines of Resolution (LR)
    """
    fr = sample_rate / 2.0
    res = sample_rate / len(fft_points) if len(fft_points) > 0 else 0
    lr = len(fft_points)  # Lines of resolution
    
    return {
        "Res": res,
        "FR": fr,
        "LR": lr,
        "SR": sample_rate,
        "RPM": rpm,
        "Win": "Hann"
    }