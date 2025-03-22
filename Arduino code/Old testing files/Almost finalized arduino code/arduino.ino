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
} weight = {0, 0};
double drankWater = 0;

struct StWeight{
  double weight;
  bool stable;
} stWeight;
bool lifted = false;

double getWeight();
bool cupLifted();
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
    // weight.current = getWeight();

    if (noWeight() && !lifted)
    {
        lifted = true;
        Serial.println("lifted");
        // In case cup is removed, do the following:
    }
    while(lifted && !noWeight()){
      stableWeight();
      if(stWeight.stable){
        weight.current = stWeight.weight;
        Serial.println(String(weight.current));
        lifted = false;
      }
    }

    if (weight.current < weight.high){
      drankWater += weight.high - weight.current;
      // HM10.print("Wtr:" + String(int(drankWater * 1000)));
      Serial.println("Wtr:" + String(int(drankWater * 1000)));
    }
    weight.high = weight.current;
    return;
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
  
    do {
      stableWeight();
    }
    while(!stWeight.stable);
    return (stWeight.weight <= 0.01);
}