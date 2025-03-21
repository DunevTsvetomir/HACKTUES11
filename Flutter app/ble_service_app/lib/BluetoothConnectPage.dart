import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_reactive_ble/flutter_reactive_ble.dart';
import 'package:font_awesome_flutter/font_awesome_flutter.dart';

class BluetoothConnectPage extends StatefulWidget {
  const BluetoothConnectPage({super.key});

  @override
  State<BluetoothConnectPage> createState() => _BluetoothConnectPageState();
}

class _BluetoothConnectPageState extends State<BluetoothConnectPage> {
  final flutterReactiveBle = FlutterReactiveBle();
  late Stream<DiscoveredDevice> _scanStream;
  final List<DiscoveredDevice> _devices = []; //!!!!
  late StreamSubscription<DiscoveredDevice> _scanSubscription;
  bool _isScanning = false;
  late StreamSubscription<ConnectionStateUpdate> _connectionSubscription;
  String _connectionStatus = "Not connected";

  void startScan() {
    _devices.clear();
    setState(() {
      _isScanning = true;
    });
    _scanSubscription = flutterReactiveBle.scanForDevices(
      withServices: [],
      scanMode: ScanMode.lowLatency,
    ).listen((device) {
      if (!_devices.any((d) => d.id == device.id)) {
        setState(() {
          _devices.add(device);
        });
      }
    }, onError: (err) {
      setState(() {
        _isScanning = false;
      });
    });
  }

  void stopScan() {
    _scanSubscription.cancel();
    setState(() {
      _isScanning = false;
    });
  }

  void connectToDevice(DiscoveredDevice device) {
    stopScan();
    setState(() {
      _connectionStatus = "Connecting to ${device.name}...";
    });

    _connectionSubscription = flutterReactiveBle.connectToDevice(
      id: device.id,
      connectionTimeout: const Duration(seconds: 10),
    ).listen((update) {
      if (update.connectionState == DeviceConnectionState.connected) {
        setState(() {
          _connectionStatus = "Connected to ${device.name}";
        });
      } else if (update.connectionState == DeviceConnectionState.disconnected) {
        setState(() {
          _connectionStatus = "Disconnected";
        });
      }
    }, onError: (err) {
      setState(() {
        _connectionStatus = "Connection failed";
      });
    });
  }

  @override
  void dispose() {
    _scanSubscription.cancel();
    _connectionSubscription.cancel();
    super.dispose();
  }

  @override
  void initState() {
    super.initState();
    startScan();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Bluetooth",  style: TextStyle(fontSize: 23, fontWeight: FontWeight.bold),),
        backgroundColor: Colors.indigoAccent,
        actions: [
          IconButton(
            icon: Icon(
              _isScanning ? Icons.stop : FontAwesomeIcons.arrowsRotate,
              color: _isScanning ? Colors.black : Colors.black,
              size: 25,
            ),
            onPressed: () {
              if (_isScanning) {
                stopScan();
              } else {
                startScan();
              }
            },
          )
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12.0),
            child: Text(
              _connectionStatus,
              style: const TextStyle(fontSize: 16, color: Colors.indigo),
            ),
          ),
          Expanded(
            child: ListView.builder(
              itemCount: _devices.length,
              itemBuilder: (context, index) {
                final device = _devices[index];
                return ListTile(
                  title: Text(device.name.isNotEmpty ? device.name : "Unknown Device"),
                  subtitle: Text("RSSI: ${device.rssi}"),
                  trailing: const Icon(Icons.bluetooth),
                  onTap: () => connectToDevice(device),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}