# Hamit Batuhan Aydin, stud. M.Sc. Music Acoustic 
# 20.08.2026
# Simple frequency response measurement using an audio interface.
# Includes sweep generation, latency calibration, repeated measurements,
# reference comparison, and FRF plotting.
import os
import sounddevice as sd
import numpy as np
import matplotlib.pyplot as plt

from scipy.signal import chirp, correlate, correlation_lags
from scipy.io import savemat, loadmat


# Measurement settings
fs = 48000
amp = 0.7
averages = 3
duration = 5
device = "none"

os.makedirs("results", exist_ok=True)


# Record audio and check for buffer errors
def record(x):
    y = np.zeros(len(x))
    position = 0
    audio_error = False

    def callback(indata, outdata, frames, time, status):
        nonlocal position, audio_error

        if status.output_underflow or status.input_overflow:
            audio_error = True

        end = min(position + frames, len(x))
        count = end - position

        outdata.fill(0)

        if count > 0:
            outdata[:count, 0] = x[position:end]
            y[position:end] = indata[:count, 0]

        position = end

        if position >= len(x):
            raise sd.CallbackStop

    with sd.Stream(
        device=(device, device),
        samplerate=fs,
        channels=(1, 1),
        blocksize=512,
        dtype="float64",
        callback=callback
    ):
        sd.sleep(int((len(x) / fs + 0.2) * 1000))

    return y, audio_error


# Latency calibration
def calibrate():
    input("Connect Output 1 -> Input 1. ENTER...")

    noise = np.random.randn(fs)
    noise *= amp / np.max(np.abs(noise))

    pre = np.zeros(fs // 2)
    x = np.r_[pre, noise, pre]

    y, _ = record(x)

    # Find where the recorded noise starts
    c = correlate(y, noise, mode="full")
    lags = correlation_lags(len(y), len(noise), mode="full")

    latency = lags[np.argmax(np.abs(c))] - len(pre)

    print(
        f"Latency: {latency} samples "
        f"({latency/fs*1000:.1f} ms)"
    )

    return latency


# Make sweep
def make_sweep():
    # Log sweep from 20 Hz to 20 kHz
    t = np.arange(duration * fs) / fs

    sweep = amp * chirp(
        t,
        f0=20,
        f1=20000,
        t1=duration,
        method="logarithmic"
    )

    # Silence before and after
    return np.r_[
        np.zeros(fs // 2),
        sweep,
        np.zeros(fs)
    ]


# Run measurement
def measure(x, latency):
    runs = []
    i = 1

    while i <= averages:
        print(f"Measurement {i}/{averages}")

        temp, audio_error = record(x)

        # Ignore bad recordings and try again
        if audio_error:
            print("Audio error - retrying...")
            continue

        runs.append(temp[latency:])
        i += 1

    # Average the good recordings
    y = np.mean(runs, axis=0)

    peak = 20 * np.log10(np.max(np.abs(y)))
    print(f"Peak: {peak:.1f} dBFS")

    return y


# Plot frequency response
def plot_frf(ref, meas):
    n = min(len(ref), len(meas))

    ref = ref[:n]
    meas = meas[:n]

    # FFT - rfft keeps only positive frequencies
    REF = np.fft.rfft(ref)
    MEAS = np.fft.rfft(meas)

    # Frequency axis
    f = np.fft.rfftfreq(n, 1 / fs)

    # Measurement compared with reference
    H = MEAS / REF
    dB = 20 * np.log10(np.abs(H))

    # Show only 20 Hz - 20 kHz
    m = (f >= 20) & (f <= 20000)

    fig, ax = plt.subplots(figsize=(7, 3.5))

    ax.semilogx(
        f[m],
        dB[m],
        linewidth=1.5
    )

    # 0 dB reference line
    ax.axhline(
        0,
        linestyle="--",
        linewidth=1.2,
        color="red"
    )

    # Automatic y-axis with 5 dB margin
    ymin = np.min(dB[m])
    ymax = np.max(dB[m])

    if ymin > 0:
        ax.set_ylim(-5, ymax + 5)

    elif ymax < 0:
        ax.set_ylim(ymin - 5, 5)

    else:
        ax.set_ylim(ymin - 5, ymax + 5)

    ax.set_xlim(20, 20000)
    ax.grid(True, which="both")

    ax.tick_params(labelsize=16)

    for spine in ax.spines.values():
        spine.set_linewidth(1.2)

    ax.set_xlabel("Frequency [Hz]", fontsize=18)
    ax.set_ylabel("Gain [dB]", fontsize=18)
    ax.set_title("Frequency Response", fontsize=19)

    # Reduce empty space around the plot
    fig.subplots_adjust(
        left=0.08,
        bottom=0.18,
        right=0.98,
        top=0.90
    )

    plt.show()


# Main menu
while True:

    choice = input(
        "\n1: New measurement"
        "\n2: Compare measurements"
        "\n3: Exit"
        "\nSelect: "
    )

    if choice == "1":

        # Audio device
        answer = input(
            "Configure audio settings? (y/n): "
        )

        if answer.lower() == "y":
            devices = sd.query_devices()

            for i, d in enumerate(devices):
                print(
                    f"{i}: {d['name']} "
                    f"(in:{d['max_input_channels']}, "
                    f"out:{d['max_output_channels']})"
                )

            device = int(
                input("Select device number: ")
            )

        if isinstance(device, int):
            print(
                "Selected device:",
                sd.query_devices(device)["name"]
            )
        else:
            print("Selected device:", device)

        # Latency calibration
        latency = calibrate()

        # Run measurement
        sweep = make_sweep()

        input(
            "Connect setup and press ENTER..."
        )

        signal = measure(
            sweep,
            latency
        )

        # Save measurement
        name = input("Measurement name: ")

        savemat(
            os.path.join(
                "results",
                name + ".mat"
            ),
            {"signal": signal}
        )

        print(f"Saved: {name}.mat")


    elif choice == "2":

        # Show saved measurements
        files = sorted([
            f for f in os.listdir("results")
            if f.endswith(".mat")
        ])

        if len(files) < 2:
            print("Not enough measurements.")
            continue

        print("\nAvailable measurements:")

        for i, file in enumerate(files, 1):
            print(f"{i}: {file}")

        r = int(
            input("Reference number: ")
        )

        m = int(
            input("Measurement number: ")
        )

        ref = loadmat(
            os.path.join(
                "results",
                files[r - 1]
            )
        )["signal"].squeeze()

        meas = loadmat(
            os.path.join(
                "results",
                files[m - 1]
            )
        )["signal"].squeeze()

        plot_frf(ref, meas)


    elif choice == "3":
        break

    else:
        print("Invalid selection.")
