#include <LiquidCrystal.h>

LiquidCrystal lcd(12, 11, 10, 9, 8, 7);

double cupWeight;
bool gotCupWeight = false;
bool liftedCup = false;
double totalWater;
double newWater;
double waterDrank = 0;
int timesDrank = 0;
bool gotTotalWater = false;

void setup()
{
  analogWrite(6, 0); //LCD Contrast
  lcd.begin(16, 2);
  pinMode(A0, INPUT); //Water Weight
  pinMode(2, INPUT_PULLUP);  //Reset Button
  pinMode(3, INPUT_PULLUP);  //Cup Weight
  pinMode(4, INPUT_PULLUP); //Get initial water

  #define calibration_factor 450000
  #define LOADCELL_DOUT_PIN 5
  #define LOADCELL_SCK_PIN 13
}

void loop()
{
  if(digitalRead(2) == LOW)  //Calibrate for new cup and reset water drank
  {
    gotCupWeight = false;
    gotTotalWater = false;
    waterDrank = 0;
  }

  while(digitalRead(3) == HIGH && !gotCupWeight)
  {
    lcd.print("Put empty cup");
    delay(10);
    cupWeight = analogRead(A0);
    if(digitalRead(3) == LOW)gotCupWeight = true;
    lcd.clear();
  }
  
  while(!gotTotalWater)
  {
  lcd.print("Pour water in");
  delay(10);
  totalWater = analogRead(A0) - cupWeight;
  newWater = totalWater;
  if(totalWater <= 0)totalWater = 0;
  if(digitalRead(4) == LOW)gotTotalWater = true;
  lcd.clear();
  }

  int i = 0;
  while(analogRead(A0) < 0.01)  //Check if cup is lifted
  {
    for(; i < 1; i++)
    {
      timesDrank++;
      liftedCup = true;
    }
  }

if(analogRead(A0) >= cupWeight - 0.01 && liftedCup)
  {
    lcd.setCursor(14, 0);
    lcd.print("OK");
    do
    {
    lcd.setCursor(14, 1);
    lcd.print("OK");
    newWater = analogRead(A0) - cupWeight;
    if(newWater < 0)newWater = 0;
    }while(analogRead(A0) - cupWeight >= newWater);
    waterDrank += totalWater - newWater;
    liftedCup = false;
  }

  while(analogRead(A0) - cupWeight > totalWater)totalWater = analogRead(A0) - cupWeight;
  if(newWater < totalWater)totalWater = newWater;
  //totalWater = newWater;

  lcd.setCursor(0, 0);
  lcd.print(totalWater);
  lcd.setCursor(8, 0);
  lcd.print(newWater);
  lcd.setCursor(0, 1);
  lcd.print(waterDrank);
  lcd.setCursor(8, 1);
  lcd.print(timesDrank);
  delay(1000);
  lcd.clear();
  delay(10);
}