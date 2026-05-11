import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';
import 'dart:convert';

import '../models/prediction.dart';

class ApiService {
  // 10.0.2.2 = localhost del emulador Android
  // localhost  = desktop / web / dispositivo físico en la misma red
  static const String _baseUrl = 'http://localhost:8000';

  Future<PredictionResponse> predict(XFile imageFile) async {
    final uri = Uri.parse('$_baseUrl/api/v1/predict');
    final bytes = await imageFile.readAsBytes();
    final request = http.MultipartRequest('POST', uri)
      ..files.add(http.MultipartFile.fromBytes(
        'file',
        bytes,
        filename: imageFile.name,
      ));

    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);

    if (response.statusCode != 200) {
      throw Exception('Prediction failed: ${response.body}');
    }

    return PredictionResponse.fromJson(jsonDecode(response.body));
  }
}
