import 'dart:io';
import 'package:flutter/material.dart';

import '../models/prediction.dart';

class ResultScreen extends StatelessWidget {
  final File imageFile;
  final PredictionResponse prediction;

  const ResultScreen({
    super.key,
    required this.imageFile,
    required this.prediction,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Results')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: Image.file(imageFile, width: double.infinity, fit: BoxFit.cover),
            ),
            const SizedBox(height: 20),
            if (prediction.detections.isEmpty)
              const Center(child: Text('No lesions detected.'))
            else ...[
              Text(
                '${prediction.detections.length} detection(s)',
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: 12),
              ...prediction.detections.map((d) => _DetectionCard(detection: d)),
            ],
          ],
        ),
      ),
    );
  }
}

class _DetectionCard extends StatelessWidget {
  final Detection detection;
  const _DetectionCard({required this.detection});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            CircleAvatar(
              backgroundColor: Theme.of(context).colorScheme.primaryContainer,
              child: Text(
                detection.classCode.toUpperCase().substring(0, 2),
                style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(detection.className,
                      style: const TextStyle(fontWeight: FontWeight.w600)),
                  Text('Code: ${detection.classCode}',
                      style: const TextStyle(color: Colors.grey, fontSize: 12)),
                ],
              ),
            ),
            Text(
              '${(detection.confidence * 100).toStringAsFixed(1)}%',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: detection.confidence > 0.7
                    ? Colors.green
                    : Colors.orange,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
