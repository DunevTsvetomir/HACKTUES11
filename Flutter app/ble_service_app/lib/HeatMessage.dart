import 'package:flutter/material.dart';
import 'package:flutter_reactive_ble/flutter_reactive_ble.dart';
import 'dart:async';

class BluetoothConnectPage extends StatefulWidget {
  const BluetoothConnectPage({super.key});

  @override
  _BluetoothConnectPageState createState() => _BluetoothConnectPageState();
}

class _BluetoothConnectPageState extends State<BluetoothConnectPage> {
  final flutterReactiveBle = FlutterReactiveBle();
  late StreamSubscription<DiscoveredDevice> _scanSubscription;
  late StreamSubscription<ConnectionStateUpdate> _connectionSubscription;
  final List<DiscoveredDevice> _devices = [];
  bool _isScanning = false;
  DiscoveredDevice? _connectedDevice;
  QualifiedCharacteristic? _writeCharacteristic;

  void startScan() {
    setState(() {
      _devices.clear();
      _isScanning = true;
    });

    _scanSubscription = flutterReactiveBle.scanForDevices(withServices: []).listen((device) {
      if (!_devices.any((d) => d.id == device.id)) {
        setState(() => _devices.add(device));
      }
    }, onDone: () => setState(() => _isScanning = false));
  }

  void stopScan() {
    _scanSubscription.cancel();
    setState(() => _isScanning = false);
  }

  void connectToDevice(DiscoveredDevice device) {
    _connectionSubscription = flutterReactiveBle.connectToDevice(id: device.id).listen((update) {
      if (update.connectionState == DeviceConnectionState.connected) {
        setState(() {
          _connectedDevice = device;
          _writeCharacteristic = QualifiedCharacteristic(
            deviceId: device.id,
            serviceId: Uuid.parse("0000FFE0-0000-1000-8000-00805F9B34FB"),
            characteristicId: Uuid.parse("0000FFE1-0000-1000-8000-00805F9B34FB"),
          );
        });
      }
    });
  }

  void sendCommand(String command) async {
    if (_writeCharacteristic != null) {
      await flutterReactiveBle.writeCharacteristicWithResponse(
        _writeCharacteristic!,
        value: command.codeUnits,
      );
      print("Sent: $command");
    } else {
      print("No connected device");
    }
  }

  @override
  void dispose() {
    _scanSubscription.cancel();
    _connectionSubscription.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Bluetooth Connect"),
        actions: [
          IconButton(
            icon: Icon(_isScanning ? Icons.stop : Icons.bluetooth_searching),
            onPressed: _isScanning ? stopScan : startScan,
          )
        ],
      ),
      body: ListView(
        children: _devices.map((device) => ListTile(
          title: Text(device.name.isNotEmpty ? device.name : device.id),
          onTap: () {
            connectToDevice(device);
            Navigator.pop(context);
          },
        )).toList(),
      ),
    );
  }
}

class HomePage extends StatelessWidget {
  final FlutterReactiveBle flutterReactiveBle;
  final QualifiedCharacteristic? writeCharacteristic;

  const HomePage({required this.flutterReactiveBle, required this.writeCharacteristic, super.key});

  void sendCommand(BuildContext context, String command) async {
    if (writeCharacteristic != null) {
      await flutterReactiveBle.writeCharacteristicWithResponse(
        writeCharacteristic!,
        value: command.codeUnits,
      );
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Sent: $command")));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("Control Panel"),
        actions: [
          IconButton(
            icon: const Icon(Icons.bluetooth),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (context) => BluetoothConnectPage()),
              );
            },
          ),
        ],
      ),
      body: Center(
        child: ElevatedButton(
          child: const Text("HEAT"),
          onPressed: () => sendCommand(context, "heat"),
        ),
      ),
    );
  }
}
