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

    startWeight = scale.get_units

    scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
    scale.set_scale(calibration_factor); // This value is obtained by using the SparkFun_HX711_Calibration sketch
    scale.tare();                        // Assuming there is no weight on the scale at start up, reset the scale to 0

    pinMode(2, INPUT_PULLUP); // Reset Button
    pinMode(3, INPUT_PULLUP); // Cup Weight

    pinMode(4, OUTPUT); // Test LED
}

void loop()
{
    HM10.listen();
    if (cupLifted() && !lifted)
    {
        lifted = true;
        // in case cup is removed we do the following:
        digitalWrite(heat, LOW);
        water.times++;
        water.amount += weight.last - weight.current;
        HM10.println("DrnkWtr: " water.amount);
        HM10.println("TmsDrnk: " water.times);
    }
    // weight.current = getWeight();
    //if(getWeight()>weight.current)
    if (weight.current >= weight.last)
    {
        weight.last = weight.current;
        water.times--; // Because of wrongful adding when the cup was lifted before refilling
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
    switch (inData)
    {
    case "":
    default:
        break;
    case "heat":
        heat();
        break;
    }

    unsigned double getWeight()
    {
        return scale.get_units;
    }
    bool cupLifted()
    {
        return (getWeight() <= 0.005);
    }

    void heat()
    {
        digitalWrite(heat, HIGH);
    }

    bool isStable(){
        stable = true;
        unsigned int weight = getWeight();
        if(weight!=getWeight())
    }
}
