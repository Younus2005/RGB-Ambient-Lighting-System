# RGB Ambient Lighting System

A **real-time PC ambient lighting system** that synchronizes RGB LEDs with:

- Screen colors (Ambilight style)
- Music and system audio
- Hybrid visual effects

The project uses **Python for PC-side processing** and **Arduino for LED control**.

The system captures audio frequencies and screen colors in real time and maps them to a **64-LED circular lighting layout**.

---

# Features

• Screen Ambilight mode (edge sampling)  
• Music reactive lighting using FFT  
• Hybrid screen + audio mode  
• Manual RGB control mode  
• Cinematic HDR tone mapping  
• Lightning, particle, fog, and shockwave effects  
• GUI control panel  
• High performance (90 FPS)

---

# System Architecture
PC (Python Software)
│
├─ Screen capture (mss)
├─ Audio processing (FFT)
├─ Lighting effect engine
└─ Serial communication
│
▼

Arduino UNO
│
└─ Controls WS2812B LED strip / RGB fans

---

# Hardware Requirements

| Component | Quantity |
|--------|--------|
| Arduino UNO | 1 |
| WS2812B LED strip / RGB fans | 64 LEDs |
| 5V Power Supply | 5A recommended |
| USB cable | 1 |
| 330Ω resistor | 1 |
| 1000µF capacitor | 1 |

---

# LED Layout

The project uses **64 LEDs arranged in four fan sections**.

```
Fan 1 → LED 0-15
Fan 2 → LED 16-31
Fan 3 → LED 32-47
Fan 4 → LED 48-63
```

Circular mapping:

```
LEFT  → LEDs 0-15
TOP   → LEDs 16-31
RIGHT → LEDs 32-47
BOTTOM→ LEDs 48-63
```

This layout allows the **screen mode to map colors to monitor edges**.

---

# Wiring / Connections

## LED Strip to Arduino

| LED Pin | Connect To |
|------|------|
| DIN | Arduino Pin 6 |
| 5V | External 5V power supply |
| GND | Arduino GND |

---

## Protection Components

### Data Resistor

Use a **330Ω resistor** between:

```
Arduino Pin 6 → LED DIN
```

This protects the LED data line.

---

### Power Capacitor

Add a **1000µF capacitor** between:

```
LED 5V → LED GND
```

This prevents power spikes when LEDs change brightness.

---

# Power Requirements

Each WS2812B LED can draw **up to 60mA at full brightness**.

For 64 LEDs:

```
64 × 60mA ≈ 3.8A
```

Recommended power supply:

```
5V 5A
```

⚠ Do **NOT power the LEDs directly from Arduino**.

Use an external power supply and **connect the grounds together**.

```
Power Supply GND → LED GND → Arduino GND
```

---

# Arduino Pin Layout

| Arduino Pin | Function |
|------|------|
| Pin 6 | LED Data |
| 5V | External power reference |
| GND | Ground |

Example configuration in Arduino code:

```cpp
#define DATA_PIN 6
#define NUM_LEDS 64
