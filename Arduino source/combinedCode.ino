#include "HX711.h"
#include <SoftwareSerial.h>

SoftwareSerial HM10(2, 3);
char appData;
String inData = "";

#define calibration_factor 450000 // This value is obtained using the SparkFun_HX711_Calibration sketch
#define LOADCELL_DOUT_PIN 3
#define LOADCELL_SCK_PIN 2
#define heat 6
HX711 scale;

// int cupWeight;
// bool gotCupWeight = false;
struct {
    unsigned int last;
    unsigned int current;
} weight = {0, 0};
struct {
    unsigned int amount;
    unsigned int times;
} water = {0, 0};
bool lifted = false;

unsigned double getWeight();
bool cupLifted();
void heat();
bool isStable();

void setup()
{
    Serial.begin(9600);
    HM10.begin(9600);

    scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
    scale.set_scale(calibration_factor); // This value is obtained by using the SparkFun_HX711_Calibration sketch
    scale.tare();                        // Assuming there is no weight on the scale at start up, reset the scale to 0

    pinMode(heat, OUTPUT); // Heating element
    pinMode(2, INPUT_PULLUP); // Reset Button
    pinMode(3, INPUT_PULLUP); // Cup Weight

    pinMode(4, OUTPUT); // Test LED
}

void loop()
{
    HM10.listen();
    weight.current = getWeight();

    if (cupLifted() && !lifted)
    {
        lifted = true;
        // In case cup is removed, do the following:
        digitalWrite(heat, LOW);
        water.times++;
        water.amount += weight.last - weight.current;
        HM10.println("DrnkWtr: " + String(water.amount));
        HM10.println("TmsDrnk: " + String(water.times));
    }

    if (weight.current >= weight.last)
    {
        weight.last = weight.current;
        water.times--; // Correct wrongful increment when the cup was lifted before refilling
    }

    while (HM10.available() > 0)
    {
        inData = HM10.readString();
    }
    if (Serial.available())
    {
        delay(10);
        HM10.write(Serial.read());
    }
    if (inData == "heat")
    {
        heat();
    }
    inData = ""; // Clear the command after processing
}

unsigned double getWeight()
{
    return scale.get_units();
}

bool cupLifted()
{
    return (getWeight() <= 0.005); // Adjust threshold as needed
}

void heat()
{
    digitalWrite(heat, HIGH);
    delay(5000); // Keep heating for 5 seconds (adjust as needed)
    digitalWrite(heat, LOW);
}

bool isStable()
{
    bool stable = true;
    unsigned double initialWeight = getWeight();
    for(int i = 0; i < 10; i++)
    {
      if (abs(initialWeight - getWeight()) > 0.01) // Adjust stability threshold as needed
      {
          stable = false;
      }
      delay(500); // Wait for half a second
    }
    return stable;
}
