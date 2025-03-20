#include "HX711.h"
#include <SoftwareSerial.h>


SoftwareSerial HM10(2, 3);
char appData;  
String inData = "";



#define calibration_factor 450000 //This value is obtained using the SparkFun_HX711_Calibration sketch
#define LOADCELL_DOUT_PIN  3
#define LOADCELL_SCK_PIN  2
#define heat 6;
HX711 scale;


//int cupWeight;
//bool gotCupWeight = false;
unsigned int drankWater = 0;
unsigned int maxWeight = 0;
unsigned int weight;
unsigned int timesDrank = 0;
bool lifted = false;

unsigned double getWeight();
bool cupLifted();
void heat();

void setup()
{
   Serial.begin(9600);

  startWeight = scale.get_units


  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  scale.set_scale(calibration_factor); //This value is obtained by using the SparkFun_HX711_Calibration sketch
  scale.tare(); //Assuming there is no weight on the scale at start up, reset the scale to 0

  pinMode(2, INPUT_PULLUP);  //Reset Button
  pinMode(3, INPUT_PULLUP);  //Cup Weight

  pinMode(4, OUTPUT); //Test LED
}

void loop()
{
  HM10.listen();
  if(cupLifted()&&!lifted){
    lifted = true;
    //in case cup is removed we do the following:
    digitalWrite(heat, LOW);
    timesDrank++;
    //drankWater += 
  }
  weight = getWeight()
  if(weight>=maxWeight){
    maxWeight = weight;
    timesDrank--; //Because of wrongful adding when the cup was lifted before refilling
  }
 
  while (HM10.available() > 0) {  
    inData = HM10.readString();
  }
    if (Serial.available()) {           
    delay(10);
    HM10.write(Serial.read());
  }
  switch(inData){
    case "":default:break;
    case "heat":
      heat();
      break;
    case "drankWater":
      HM10.println("DrnkWtr: "drankWater);
      break;
  }
  











  



  /*if(digitalRead(2) == LOW)  //Calibrate for new cup and reset water drank
  {
    gotCupWeight = false;
    waterDrank = 0;
  }

  while(digitalRead(3) == HIGH && gotCupWeight == false)
  {
    lcd.print("Put empty cup");
    delay(10);
    cupWeight = analogRead(A0);
    if(digitalRead(3) == LOW)gotCupWeight = true;
    lcd.clear();
  } 

  totalWater = analogRead(A0) - cupWeight;
  if(totalWater <= 0)totalWater = 0;

  while(analogRead(A0) < 10)
  {
    if(analogRead(A0) >= cupWeight && analogRead(A0) < totalWater + cupWeight)
    {
      timesDrank++;
      newWater = analogRead(A0) - cupWeight;
      waterDrank += totalWater - newWater;
      totalWater = newWater;
      break;
    }
    if(analogRead(A0) >= cupWeight && analogRead(A0) > totalWater + cupWeight)
    {
      newWater = analogRead(A0) - cupWeight;
      totalWater = newWater;
      break;
    }
  }

  lcd.print(newWater);
  delay(1000);
  lcd.clear();
  delay(10);*/

  unsigned double getWeight(){
    return scale.get_units;
  }
  bool cupLifted(){
    return (getWeight() <= 0.005);
  }

  void heat(){
    digitalWrite(heat, HIGH);
  }

}
