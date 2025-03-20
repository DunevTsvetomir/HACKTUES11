#include <SoftwareSerial.h>
SoftwareSerial HM10(2, 3);
char appData;  
String inData = "";
void setup()
{
  Serial.begin(9600);
  Serial.println("HM10 serial started at 9600");
  HM10.begin(9600); 
  pinMode(13, OUTPUT); 
  digitalWrite(13, LOW);
}
void loop()
{
  HM10.listen();
  while (HM10.available() > 0) {  
    appData = HM10.read();
    inData = String(appData); 
    Serial.write(appData);
  }
  if (Serial.available()) {           
    delay(10);
    HM10.write(Serial.read());
  }
  if ( inData == "F") {
    Serial.println("LED OFF");
    digitalWrite(13, LOW); 
    delay(500);
  }
  if ( inData == "N") {
    Serial.println("LED ON");
    digitalWrite(13, HIGH); 
    delay(500);
    digitalWrite(13, LOW); 
    delay(500);
  }

}
