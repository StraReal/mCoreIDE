#include <MeMCore.h>
#include <Arduino.h>
#include <Wire.h>
#include <SoftwareSerial.h>

MeUltrasonicSensor ultrasonic(3);
MeDCMotor motor_l(9);
MeDCMotor motor_r(10);
MeRGBLed led(7, 2);
// 0 is both leds, 1 is right, 2 is left

void _loop();
void move(int direction, int speed) {
  int leftSpeed = 0;
  int rightSpeed = 0;
  if(direction == 1) {
    leftSpeed = speed;
    rightSpeed = speed;
  } else if(direction == 2) {
    leftSpeed = -speed;
    rightSpeed = -speed;
  } else if(direction == 3) {
    leftSpeed = -speed;
    rightSpeed = speed;
  } else if(direction == 4) {
    leftSpeed = speed;
    rightSpeed = -speed;
  }
  motor_l.run((9) == M1 ? -(leftSpeed) : (leftSpeed));
  motor_r.run((10) == M1 ? -(rightSpeed) : (rightSpeed));
}

void _delay(float seconds) {
  long endTime = millis() + seconds * 1000;
  while(millis() < endTime) _loop();
}

void setup() {
  while(1) {
      if(15 < ultrasonic.distanceCm()){
        led.setColor(0, 255, 255, 255);
        move(1, 50 / 100.0 * 255);

      }else{
        led.setColor(0, 255, 0, 0);
        move(4, 50 / 100.0 * 255);
        _delay(0.1);
        move(4, 0);

      }
      led.show();

      _loop();
  }

}

void _loop() {
}

void loop() {
  _loop();
}
