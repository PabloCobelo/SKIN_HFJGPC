import 'dart:io';
import 'package:http/http.dart' as http;
import 'dart:convert';

import '../models/prediction.dart';

class ApiService {
  // Change to your backend IP when testing on a physical device
  static const String _baseUrl = 'http://10.0.2.2:8000';

  Future<PredictionResponse> predict(File imageFile) async {
    final uri = Uri.parse('$_baseUrl/api/v1/predict');
    final request = http.MultipartRequest('POST', uri)
      ..files.add(await http.MultipartFile.fromPath('file', imageFile.path));

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode != 200) {
      throw Exception('Prediction failed: ${response.body}');
    }

    return PredictionResponse.fromJson(jsonDecode(response.body));
  }
}
