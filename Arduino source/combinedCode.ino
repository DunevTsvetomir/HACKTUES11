#include "HX711.h"
#include <SoftwareSerial.h>

SoftwareSerial HM10(2, 3);
char appData;
String inData = "";

#define calibration_factor 450000
#define LOADCELL_DOUT_PIN 3
#define LOADCELL_SCK_PIN 2
#define heat 6
#define buzzer 7
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
void Heat();
void isStable();

void setup()
{
    isStable();

    Serial.begin(9600);
    HM10.begin(9600);

    scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
    scale.set_scale(calibration_factor);
    scale.tare();                        

    pinMode(heat, OUTPUT); // Heating element
    pinMode(2, INPUT_PULLUP); // Reset Button
    pinMode(3, INPUT_PULLUP); // Cup Weight
    pinMode(buzzer, OUTPUT); // Buzzer 
    pinMode(4, OUTPUT); // Test LED
}

void loop()
{
    isStable();

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
        Heat();
    }
    inData = ""; // Clear the command after processing

    if(inData == "time"){
        while(weight.current > 0.01){
            digitalWrite(buzzer, HIGH);
            delay(300);
            digitalWrite(buzzer, LOW);
            delay(300);
        }
        
    }
    inData = "";
    


    
}


unsigned double getWeight()
{
    return scale.get_units();
}

bool cupLifted()
{
    return (getWeight() <= 0.005); 
}

void Heat()
{
    digitalWrite(heat, HIGH);
    delay(5000); // Keep heating for 5 seconds (adjust as needed)
    digitalWrite(heat, LOW);
}

void isStable()
{
    //Function to check if the weight is stable and then allow other code to get executed
   bool stable = false;

    while(stable == false){
        for(int i = 0; i < 10; i++){
            if(abs(initialWeight() - getWeight()) < 0.01){
            stable = true;
         } 
         delay(250);
         else stable = false;
       }
    }
}
