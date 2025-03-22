#include <LiquidCrystal.h>
#include "HX711.h"

LiquidCrystal lcd(12, 11, 10, 9, 8, 7);


#define calibration_factor 450000 //This value is obtained using the SparkFun_HX711_Calibration sketch

#define LOADCELL_DOUT_PIN  5
#define LOADCELL_SCK_PIN  13

HX711 scale;

bool gotCupWeight = false;
bool liftedCup = false;
double cupWeight;
double totalWater;
double newWater;
double waterDrank = 0;
int timesDrank = 0;
bool gotTotalWater = false;

void setup()
{
  Serial.begin(9600);

  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  scale.set_scale(calibration_factor); //This value is obtained by using the SparkFun_HX711_Calibration sketch
  scale.tare(); //Assuming there is no weight on the scale at start up, reset the scale to 0

  analogWrite(6, 0); //LCD Contrast
  lcd.begin(16, 2);
  pinMode(A0, INPUT); //Water Weight
  pinMode(2, INPUT_PULLUP);  //Reset Button
  pinMode(3, INPUT_PULLUP);  //Cup Weight
  pinMode(4, INPUT_PULLUP); //Get initial water
}

void loop()
{
  if(digitalRead(2) == LOW)  //Calibrate for new cup and reset water drank
  {
    gotCupWeight = false;
    gotTotalWater = false;
    timesDrank = 0;
    waterDrank = 0;
  }

  while(digitalRead(3) == HIGH && !gotCupWeight)
  {
    lcd.print("Put empty cup");
    delay(10);
    cupWeight = scale.get_units();
    if(digitalRead(3) == LOW)gotCupWeight = true;
    lcd.clear();
  }
  
  while(!gotTotalWater)
  {
  lcd.print("Pour water in");
  delay(10);
  totalWater = scale.get_units() - cupWeight;
  newWater = totalWater;
  if(totalWater <= 0)totalWater = 0;
  if(digitalRead(4) == LOW)gotTotalWater = true;
  lcd.clear();
  }

  int i = 0;
  while(scale.get_units() < 0.01)  //Check if cup is lifted
  {
    for(; i < 1; i++)
    {
      timesDrank++;
      liftedCup = true;
    }
  }

if (scale.get_units() >= cupWeight && liftedCup) 
{
  unsigned long stableStartTime = millis();  // Track when newWater last changed
  int lastWater = -1; // Store last recorded water value

  do 
  {
    newWater = scale.get_units() - cupWeight;
    if(newWater < 0)newWater = 0;
    if(newWater > totalWater + cupWeight)
    {
      newWater = totalWater;
      break;
    }
        // Check if newWater has changed
    if (abs(newWater - lastWater) > 1) // Allow small fluctuations
    {
      stableStartTime = millis(); // Reset timer since value changed
      lastWater = newWater;
    }
    delay(100); // Small delay to prevent rapid fluctuations
    } 
    while(millis() - stableStartTime < 2000);  // Exit if stable for 2 seconds

    waterDrank += totalWater - newWater;
    liftedCup = false;
    totalWater = newWater;
}

  while(scale.get_units() > totalWater)totalWater = scale.get_units();

  lcd.setCursor(0, 0);
  lcd.print("Water Drank:");
  lcd.print(waterDrank);
  lcd.setCursor(0, 1);
  lcd.print("Times Drank:");
  lcd.print(timesDrank);
  delay(1000);
  lcd.clear();
  delay(10);
}