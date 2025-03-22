import 'package:flutter/material.dart';

class RoundButton extends StatelessWidget {
  const RoundButton({
    super.key,
    required this.icon,
  });
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(
        horizontal: 5,
      ),
      child: CircleAvatar(
        radius: 30,
        child: Icon(
          icon,
          size: 36,
        ),
      ),
    );
  }
}