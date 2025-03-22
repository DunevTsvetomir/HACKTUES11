#include "HX711.h"
#include <SoftwareSerial.h>
#include <math.h>
#include <LiquidCrystal.h>

LiquidCrystal lcd(12, 11, 10, 9, 8, 7);

SoftwareSerial HM10(2, 3);
char appData;
String inData = "";

#define calibration_factor 450000
#define LOADCELL_DOUT_PIN 5
#define LOADCELL_SCK_PIN 13
#define heat 6
// #define buzzer 7
HX711 scale;

// int cupWeight;
// bool gotCupWeight = false;
struct {
    // bool setup;
    // double cup;
    // double last;
    // double current;

    double high;
    double current;
} weight = {false, 0, 0, 0};
double drankWater;

struct StWeight{
  double weight;
  bool stable;
} stWeight;
bool lifted = false;

double getWeight();
bool cupLifted();
bool isStable();
bool noWeight();
void stableWeight();

void setup()
{   
    Serial.begin(9600);
    HM10.begin(9600);

    scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
    scale.set_scale(calibration_factor);
    scale.tare();                        

    pinMode(2, INPUT_PULLUP); // Reset Button
    pinMode(3, INPUT_PULLUP); // Cup Weight
    // pinMode(buzzer, OUTPUT); // Buzzer 
    // pinMode(4, OUTPUT); // Test LED
}

void loop()
{
    // if(!weight.setup){
    //     lcd.print("Place empty cup on scale");
    //     Serial.println("Place empty cup");
    //     if(isStable()&&!noWeight()){
    //         weight.cup = scale.get_units();
    //         Serial.println(weight.cup);
    //         weight.setup = true;
    //     }
    // }
    // return;

    HM10.listen();
    weight.current = getWeight();

    if (noWeight() && !lifted)
    {
        lifted = true;
        // In case cup is removed, do the following:
    }
    while(lifted && !noWeight()){
      stableWeight();
      if(stWeight.stable){
        weight.current = stWeight.weight;
        lifted = false;
      }
    }

    if (weight.current < weight.high){
      drankWater += weight.high - weight.current;
      HM10.print("Wtr:" + String(int(drankWater * 1000)))
    }
    weight.high = weight.current

    while (HM10.available() > 0)
    {
        inData = HM10.readString();
    }
    if (Serial.available())
    {
        delay(10);
        HM10.write(Serial.read());
    }


    // if(inData == "time"){
    //     while(weight.current > 0.01){
    //         digitalWrite(buzzer, HIGH);
    //         delay(300);
    //         digitalWrite(buzzer, LOW);
    //         delay(300);
    //     }
        
    // }
    inData = "";

}


double getWeight()
{
    return scale.get_units();
}

bool isStable()
{
    //Function to check if the weight is stable and then allow other code to get executed
   bool stable = false;
  
        for(int i = 0; i < 10 && stable == false; i++){
          weight.current = getWeight();
            if(fabs(weight.last - weight.current) < 0.05){
              stable = true;
            }
            else stable = false;
            delay(500);
         }
    
    return stable;
}

void stableWeight(){
  double start = getWeight();
  double weight;
  stWeight.stable = true;
  for(int i = 0; i<10;i++){
    weight = getWeight();
    if(fabs(weight-start)>0.01){
      stWeight.stable = false;
      return;
    }
  }
  stWeight.weight = weight;
}

bool noWeight(){
    return (getWeight() <= 0.01);
}