#include <SoftwareSerial.h>
SoftwareSerial HM10(0, 1); // RX = 0 (Arduino TX), TX = 1 (Arduino RX)
String inData = ""; // Buffer to store incoming data
String messages[] = {"Message 1", "Message 2", "Message 3", "Message 4", "Message 5", 
                     "Message 6", "Message 7", "Message 8", "Message 9"};

void sendATCommand(String command) {
  Serial.print("Sending AT Command: "); // Debug statement
  Serial.println(command);
  HM10.println(command);
  delay(500); // Wait for the module to process the command
  while (HM10.available()) {
    Serial.write(HM10.read()); // Print the response to the Serial Monitor
  }
}

void processMessage(String message) {
  Serial.print("Processing message: ");
  Serial.println(message); // Output the received message to the serial monitor
  for (int i = 0; i < sizeof(messages) / sizeof(messages[0]); i++) {
    if (message.startsWith(messages[i])) {
      Serial.print("Received valid message: ");
      Serial.println(messages[i]);
      return;
    }
  }
  Serial.println("Unknown or invalid message");
}

void setup() {
  Serial.begin(9600);
  while (!Serial) {
    ; // Wait for the serial port to connect (for boards like Leonardo)
  }
  Serial.println("Serial communication initialized"); // Debug statement
  Serial.println("HM10 serial started at 9600");
  HM10.begin(9600); // Set HM10 serial at 9600 baud rate

  // Debugging: Check if HM10 is responding
  sendATCommand("AT"); // Test communication

  // Configure the HM-10 module
  sendATCommand("AT+ROLE0");    // Set to peripheral mode
  sendATCommand("AT+ADTY3");    // Set advertising type to general advertising
  sendATCommand("AT+IMME0");    // Enable auto-advertising on power-up
  sendATCommand("AT+ADVI4");    // Set advertising interval to 4 (fast advertising)
  sendATCommand("AT+NAMEHM10"); // Set a custom name for the module
  sendATCommand("AT+RESET");    // Restart the module to apply changes

  pinMode(13, OUTPUT); // Onboard LED
  digitalWrite(13, LOW); // Switch OFF LED
  Serial.println("Setup complete"); // Debug statement
}

void loop() {
  // Debugging: Check if HM10.available() is being called
  Serial.print("HM10 available bytes: ");
  Serial.println(HM10.available()); // Debug statement

  //Serial.println("Loop running"); // Debug statement
  // Check for incoming data from the HM-10 module
  if (HM10.available()) {
    Serial.println("Data available from HM10"); // Debug statement
    while (HM10.available() > 0) {
      char receivedChar = HM10.read(); // Read one character at a time
      Serial.print("Received char: "); // Debug statement
      Serial.println(receivedChar);    // Debug statement
      inData += receivedChar;          // Append the character to the buffer
    }

    // If a newline character is received, process the message
    if (inData.endsWith("\n")) {
      Serial.print("Received from App: ");
      Serial.println(inData); // Print the full message to the Serial Monitor

      // Example: Process specific commands
      if (inData.startsWith("Message 1")) {
        Serial.println("Turning LED ON");
        digitalWrite(13, HIGH); // Turn ON the LED
      } else if (inData.startsWith("Message 2")) {
        Serial.println("Turning LED OFF");
        digitalWrite(13, LOW); // Turn OFF the LED
      } else {
        processMessage(inData); // Process messages using the list
      }

      // Clear the buffer for the next message
      inData = "";
    }
  }

  // Debugging: Check if Serial.available() is being called
  Serial.print("Serial available bytes: ");
  Serial.println(Serial.available()); // Debug statement

  // Check for user input from the Serial Monitor
  if (Serial.available()) {
    String userInput = Serial.readString();
    Serial.print("Sending to HM10: "); // Debug statement
    Serial.println(userInput);
    HM10.print(userInput); // Send the user input to the HM-10 module
  }

  delay(100); // Add a small delay for stability
}