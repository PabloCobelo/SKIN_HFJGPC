import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'screens/home_screen.dart';
import 'services/api_service.dart';

void main() {
  runApp(
    Provider<ApiService>(
      create: (_) => ApiService(),
      child: const SkinDetectorApp(),
    ),
  );
}

class SkinDetectorApp extends StatelessWidget {
  const SkinDetectorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Skin Lesion Detector',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF1976D2),
          brightness: Brightness.light,
        ),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}
