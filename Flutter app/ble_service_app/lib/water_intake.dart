import 'package:flutter/material.dart';

void main() {
  runApp(WaterTrackerApp());
}

class WaterTrackerApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      home: WaterTrackerPage(),
    );
  }
}

class WaterTrackerPage extends StatefulWidget {
  @override
  _WaterTrackerPageState createState() => _WaterTrackerPageState();
}

class _WaterTrackerPageState extends State<WaterTrackerPage> {
  double dailyGoal = 2000; // in ml
  double currentIntake = 0;
  List<String> intakeHistory = [];

  void addWater(int amount) {
    setState(() {
      currentIntake += amount;//!!!!!
      intakeHistory.insert(0, "${amount}ml - ${TimeOfDay.now().format(context)}");
    });
  }

  @override
  Widget build(BuildContext context) {
    double progress = currentIntake / dailyGoal;

    return Scaffold(
      appBar: AppBar(
        title: Text("Daily Water Intake", style: TextStyle(fontSize: 21, fontWeight: FontWeight.bold),),
        backgroundColor: Colors.blueAccent,
      ),
      body: Padding(
        padding: EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            // Circular progress
            SizedBox(height: 80),
            Center(
              child: Stack(
                alignment: Alignment.center,
                children: [
                  SizedBox(
                    height: 300,
                    width: 300,
                    child: CircularProgressIndicator(
                      value: progress > 1 ? 1 : progress,
                      strokeWidth: 30,
                      backgroundColor: Colors.grey[300],
                      valueColor: AlwaysStoppedAnimation<Color>(Colors.blue),
                    ),
                  ),
                  Column(
                    children: [
                      Text(
                        "${currentIntake.toInt()} / ${dailyGoal.toInt()} ml",
                        style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                      ),
                      Text("Water Intake", style: TextStyle(fontSize: 16, color: Colors.grey)),
                    ],
                  ),
                ],
              ),
            ),
            SizedBox(height: 30),
            SizedBox(height: 30),
            // Intake history
            Expanded(
              child: ListView.builder(
                itemCount: intakeHistory.length,
                itemBuilder: (context, index) {
                  return ListTile(
                    title: Text(intakeHistory[index]),
                    leading: Icon(Icons.local_drink, color: Colors.blueAccent),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
