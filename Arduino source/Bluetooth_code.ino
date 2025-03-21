#include <SoftwareSerial.h>
SoftwareSerial HM10(2, 3);
char appData;  
String inData = "";
int button = 12;
bool buttonPressed = false; // Tracks the button state
void setup()
{
  Serial.begin(9600);
  Serial.println("HM10 serial started at 9600");
  HM10.begin(9600);
  pinMode(13, OUTPUT); 
  pinMode(button, INPUT_PULLUP);
  delay(5000);
}
void loop()
{
  HM10.listen();
  while(HM10.available() > 0) {  
    inData = HM10.readString(); 
    if(inData!=""){
      HM10.println("From HM10: Received " + inData);
      Serial.println(inData);
    }
  }
  if(Serial.available()) {
    delay(10);
    HM10.write(Serial.read());
  }
  if(inData == "Msg1") {
    // Serial.println("LED OFF");
    digitalWrite(13, LOW); 
  }
  if(inData == "Msg2") {
    // Serial.println("LED ON");
    digitalWrite(13, HIGH); 
  }
  int buttonState = digitalRead(button);
  if (buttonState == HIGH && !buttonPressed) {
    buttonPressed = true;
    Serial.println("Button pressed");
    HM10.println("From HM10: Button pressed");
  } else if (buttonState == LOW && buttonPressed) {
    buttonPressed = false; // Reset the button state when released
  }
}