#include <SoftwareSerial.h>
SoftwareSerial HM10(2, 3); // RX = 2 (Arduino TX), TX = 3 (Arduino RX)
String inData = ""; // Buffer to store incoming data

void sendATCommand(String command) {
  HM10.println(command);
  delay(500); // Wait for the module to process the command
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
  sendATCommand("AT+ADTY3");    // Set advertising type to general advertising
  sendATCommand("AT+IMME0");    // Enable auto-advertising on power-up
  sendATCommand("AT+ADVI4");    // Set advertising interval to 4 (fast advertising)
  sendATCommand("AT+NAMEHM10"); // Set a custom name for the module
  sendATCommand("AT+RESET");    // Restart the module to apply changes

  pinMode(13, OUTPUT); // Onboard LED
  digitalWrite(13, LOW); // Switch OFF LED
}

void loop() {
  // Check for incoming data from the HM-10 module
  while (HM10.available()) {
    char receivedChar = HM10.read(); // Read one character at a time
    inData += receivedChar;          // Append the character to the buffer

    // If a newline character is received, process the message
    if (receivedChar == '\n') {
      Serial.print("Received from App: ");
      Serial.println(inData); // Print the full message to the Serial Monitor

      // Example: Process specific commands
      if (inData.startsWith("LED ON")) {
        Serial.println("Turning LED ON");
        digitalWrite(13, HIGH); // Turn ON the LED
      } else if (inData.startsWith("LED OFF")) {
        Serial.println("Turning LED OFF");
        digitalWrite(13, LOW); // Turn OFF the LED
      } else {
        Serial.println("Unknown Command");
      }

      // Clear the buffer for the next message
      inData = "";
    }
  }

  // Check for user input from the Serial Monitor
  if (Serial.available()) {
    String userInput = Serial.readString();
    HM10.print(userInput); // Send the user input to the HM-10 module
  }
}