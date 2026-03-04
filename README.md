# RGB Ambient Lighting System

Real-time PC ambient lighting system built with Python and Arduino.

## Features

- Screen Ambilight mode
- Music reactive RGB mode
- Hybrid mode
- Manual color mode
- Real-time audio FFT analysis
- Cinematic screen sampling

## Hardware Required

- Arduino UNO
- WS2812B LED strip or RGB fans
- USB connection

## Installation

Install dependencies:

pip install -r requirements.txt

Run the program:

python rgb_master.py

## Project Overview

This system captures screen colors and audio frequencies in real time
and maps them to a 64-LED circular RGB lighting system.
