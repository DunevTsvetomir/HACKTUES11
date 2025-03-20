#include <SoftwareSerial.h>
SoftwareSerial HM10(2, 3); // RX = 2, TX = 3
char appData;
String inData = "";

void sendATCommand(String command) {
  HM10.println(command);
  delay(100); // Wait for the module to process the command
  while (HM10.available()) {
    Serial.write(HM10.read()); // Print the response to the Serial Monitor
  }
}

void setup() {
  Serial.begin(9600);
  Serial.println("HM10 serial started at 9600");
  HM10.begin(9600); // Set HM10 serial at 9600 baud rate

  // Configure the HM-10 module
  sendATCommand("AT");          // Test communication
  sendATCommand("AT+ROLE0");    // Set to peripheral mode
  sendATCommand("AT+ADVI4");    // Set advertising interval
  sendATCommand("AT+NAMEHM10"); // Set a custom name
  sendATCommand("AT+RESET");    // Restart the module

  pinMode(13, OUTPUT); // Onboard LED
  digitalWrite(13, LOW); // Switch OFF LED
}

void loop() {
  HM10.listen();  // Listen to the HM10 port
  while (HM10.available() > 0) {   // If HM10 sends something, read it
    appData = HM10.read();
    inData = String(appData);  // Save the data in string format
    Serial.write(appData);
  }
  if (Serial.available()) {           // Read user input if available
    delay(10);
    HM10.write(Serial.read());
  }
  if (inData == "0") {
    Serial.println("LED OFF");
    digitalWrite(13, LOW); // Switch OFF LED
    delay(500);
  }
  if (inData == "1") {
    Serial.println("LED ON");
    digitalWrite(13, HIGH); // Switch ON LED
    delay(500);
    digitalWrite(13, LOW); // Switch OFF LED
    delay(500);
  }
}