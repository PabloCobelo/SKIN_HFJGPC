import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';
import 'dart:convert';

import '../models/prediction.dart';

class ApiService {
  static String get _baseUrl {
    if (kIsWeb) {
      final uri = Uri.base;
      final port = uri.port;
      final portStr = (port == 80 || port == 443 || port == 0) ? '' : ':$port';
      return '${uri.scheme}://${uri.host}$portStr';
    }
    return 'http://10.0.2.2:8000';
  }

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
