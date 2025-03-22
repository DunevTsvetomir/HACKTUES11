#include "HX711.h"
#include <SoftwareSerial.h>
#include <math.h>

SoftwareSerial HM10(2, 3);
char appData;
String inData = "";

#define calibration_factor 450000
#define LOADCELL_DOUT_PIN 5
#define LOADCELL_SCK_PIN 6
HX711 scale;


struct {
    double high;
    double current;
    int diff(){
      return int(1000*(this->high-this->current));
    }
} weight = {0, 0};

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
}

void loop()
{
    HM10.listen();

    if (noWeight() && !lifted)
    {
        lifted = true;
        // Serial.println("lifted");
    }
    while(lifted && !noWeight()){
      stableWeight();
      if(stWeight.stable){
        weight.current = stWeight.weight;
        //Serial.println(String(weight.current));
        lifted = false;
      }
    }

    if (weight.current < weight.high){
      HM10.print(String(weight.diff()));
      Serial.println("Drank:"+String(weight.diff()));
    }
    weight.high = weight.current;

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