#include <FastLED.h>

#define LED_PIN 6
#define NUM_LEDS 64
#define BRIGHTNESS 500

CRGB leds[NUM_LEDS];
int index_led = 0;

void setup() {
  Serial.begin(500000);   // 🚀 HIGH SPEED
  FastLED.addLeds<WS2812B, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);
  FastLED.clear();
  FastLED.show();
}

void loop() {
  while (Serial.available() >= 3) {
    byte r = Serial.read();
    byte g = Serial.read();
    byte b = Serial.read();

    leds[index_led] = CRGB(r, g, b);
    index_led++;

    if (index_led >= NUM_LEDS) {
      FastLED.show();
      index_led = 0;
    }
  }
}