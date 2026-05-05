class BoundingBox {
  final int x1, y1, x2, y2;
  const BoundingBox({
    required this.x1,
    required this.y1,
    required this.x2,
    required this.y2,
  });

  factory BoundingBox.fromJson(Map<String, dynamic> json) => BoundingBox(
        x1: json['x1'],
        y1: json['y1'],
        x2: json['x2'],
        y2: json['y2'],
      );
}

class Detection {
  final int classId;
  final String classCode;
  final String className;
  final double confidence;
  final BoundingBox bbox;

  const Detection({
    required this.classId,
    required this.classCode,
    required this.className,
    required this.confidence,
    required this.bbox,
  });

  factory Detection.fromJson(Map<String, dynamic> json) => Detection(
        classId: json['class_id'],
        classCode: json['class_code'],
        className: json['class_name'],
        confidence: (json['confidence'] as num).toDouble(),
        bbox: BoundingBox.fromJson(json['bbox']),
      );
}

class PredictionResponse {
  final List<Detection> detections;
  final int imageWidth;
  final int imageHeight;

  const PredictionResponse({
    required this.detections,
    required this.imageWidth,
    required this.imageHeight,
  });

  factory PredictionResponse.fromJson(Map<String, dynamic> json) =>
      PredictionResponse(
        detections: (json['detections'] as List)
            .map((d) => Detection.fromJson(d))
            .toList(),
        imageWidth: json['image_width'],
        imageHeight: json['image_height'],
      );
}
