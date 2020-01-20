/* This minimal example shows how to get single-shot range
measurements from the VL6180X.

The range readings are in units of mm. */

#include <Wire.h>
#include <VL6180X.h>
// Distance sensor:　https://www.st.com/ja/imaging-and-photonics-solutions/vl6180x.html
VL6180X sensor;

void setup() 
{
  Serial.begin(2000000);
  Wire.begin();
  sensor.init();
  sensor.configureDefault();
  sensor.setTimeout(500);
//  pinMode(11,OUTPUT);
}

void loop() 
{
  int distance = sensor.readRangeSingleMillimeters();
  if (sensor.timeoutOccurred() == 0) { 
    Serial.println(distance);
    }
//  delay(50);
}
