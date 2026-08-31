# FRF Measurement Tool

This folder contains simple MATLAB and Python tools for measuring the frequency response function (FRF) of audio devices.

## What it does

The tool:

- generates a logarithmic sweep from 20 Hz to 20 kHz,
- measures the system latency,
- records several measurement runs,
- rejects measurements with audio buffer errors,
- saves the measured signal,
- compares a measurement with a reference measurement,
- calculates the frequency response,
- plots the resulting gain in dB.

## Measurement principle

A reference measurement is first recorded using the same audio interface and signal path without the device under test.

The device under test is then measured with the same excitation signal.

The frequency response is calculated from the ratio between the measured spectrum and the reference spectrum:

$
H(f) = \frac{Y_\mathrm{meas}(f)}{Y_\mathrm{ref}(f)}
$

and displayed in decibels as:

\[
20\log_{10}|H(f)|
\]

Using a reference measurement compensates for the frequency response of the audio interface and the measurement signal path.

## Basic workflow

1. Connect Output 1 directly to Input 1 and run the latency calibration.
2. Make a reference measurement.
3. Connect the device under test.
4. Run the measurement again.
5. Save both measurements.
6. Select the reference and measurement files in the comparison menu.
7. The FRF is calculated and plotted.

## Files

- `FRF_measurement.m` – MATLAB implementation
- `FRF_measurement.py` – Python implementation

## Author

H. Batuhan Aydin  
stud. M.Sc. Music Acoustics  
Erich Thienhaus Institute
