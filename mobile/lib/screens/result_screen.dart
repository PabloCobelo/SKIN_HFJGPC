import 'dart:math';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:url_launcher/url_launcher.dart';

import '../models/prediction.dart';

// ── Disease metadata ──────────────────────────────────────────────────────────

class _DiseaseInfo {
  final String name;
  final String description;
  final String risk;
  final Color riskColor;
  final String symptoms;
  final String recommendation;
  final bool isHighRisk;

  const _DiseaseInfo({
    required this.name,
    required this.description,
    required this.risk,
    required this.riskColor,
    required this.symptoms,
    required this.recommendation,
    this.isHighRisk = false,
  });
}

const _diseaseData = <String, _DiseaseInfo>{
  'akiec': _DiseaseInfo(
    name: 'Queratosis Actínica',
    description:
        'Lesión precancerosa causada por exposición prolongada a la radiación UV. '
        'Afecta principalmente a personas con piel clara y de edad avanzada.',
    risk: 'Medio-Alto',
    riskColor: Colors.orange,
    symptoms:
        'Parches ásperos y escamosos, enrojecimiento, sensación de ardor o picazón.',
    recommendation:
        'Consulta con un dermatólogo. Puede requerir crioterapia, láser o medicación tópica.',
    isHighRisk: true,
  ),
  'bcc': _DiseaseInfo(
    name: 'Carcinoma Basocelular',
    description:
        'El cáncer de piel más frecuente. Crece lentamente y rara vez hace metástasis, '
        'pero puede destruir tejido local si no se trata.',
    risk: 'Alto',
    riskColor: Colors.deepOrange,
    symptoms:
        'Nódulo perlado o brillante, úlcera que no cicatriza, zona rosada o rojiza.',
    recommendation:
        'Requiere atención médica urgente. El tratamiento incluye cirugía, radioterapia o medicación tópica.',
    isHighRisk: true,
  ),
  'bkl': _DiseaseInfo(
    name: 'Queratosis Benigna',
    description:
        'Lesión benigna muy común, también llamada queratosis seborreica. '
        'Aparece con el envejecimiento y no tiene potencial maligno.',
    risk: 'Bajo',
    riskColor: Colors.green,
    symptoms:
        'Manchas de color marrón o negro, textura cérea y rugosa, bordes bien definidos.',
    recommendation:
        'Generalmente no requiere tratamiento. Se puede eliminar por estética mediante crioterapia o electrocauterización.',
  ),
  'df': _DiseaseInfo(
    name: 'Dermatofibroma',
    description:
        'Nódulo benigno del tejido conjuntivo, frecuente en extremidades. '
        'Su origen puede estar relacionado con picaduras de insectos o foliculitis.',
    risk: 'Muy Bajo',
    riskColor: Colors.teal,
    symptoms: 'Nódulo firme, pequeño, color marrón rojizo, ligeramente sensible al tacto.',
    recommendation:
        'No requiere tratamiento. Si causa molestia o duda diagnóstica, puede extirparse.',
  ),
  'mel': _DiseaseInfo(
    name: 'Melanoma',
    description:
        'El cáncer de piel más peligroso. Se origina en los melanocitos y tiene '
        'alta capacidad de metástasis si no se detecta y trata a tiempo.',
    risk: 'Muy Alto',
    riskColor: Colors.red,
    symptoms:
        'Lunar asimétrico, bordes irregulares, múltiples colores, diámetro >6 mm, evolución rápida.',
    recommendation:
        'Atención médica URGENTE. El diagnóstico temprano es crítico para el pronóstico. No demores la consulta.',
    isHighRisk: true,
  ),
  'nv': _DiseaseInfo(
    name: 'Nevo Melanocítico',
    description:
        'Lunar común benigno formado por melanocitos agrupados. '
        'La mayoría son inofensivos, aunque deben vigilarse ante cambios de forma o color.',
    risk: 'Muy Bajo',
    riskColor: Colors.teal,
    symptoms: 'Mancha o nódulo marrón uniforme, bordes regulares, sin cambios en el tiempo.',
    recommendation:
        'Revisión dermatológica periódica. Aplica la regla ABCDE para detectar cambios sospechosos.',
  ),
  'vasc': _DiseaseInfo(
    name: 'Lesión Vascular',
    description:
        'Grupo de lesiones originadas en los vasos sanguíneos de la piel, '
        'como angiomas, hemangiomas o manchas en vino de Oporto. Generalmente benignas.',
    risk: 'Bajo',
    riskColor: Colors.green,
    symptoms: 'Manchas rojizas, violáceas o azuladas, pueden ser planas o elevadas.',
    recommendation:
        'Habitualmente no requieren tratamiento. Consulta si presenta crecimiento, sangrado o cambios.',
  ),
};

// ── Screen ────────────────────────────────────────────────────────────────────

class ResultScreen extends StatelessWidget {
  final XFile imageFile;
  final PredictionResponse prediction;

  const ResultScreen({
    super.key,
    required this.imageFile,
    required this.prediction,
  });

  Detection? get _topDetection {
    if (prediction.detections.isEmpty) return null;
    return prediction.detections.reduce(
      (a, b) => a.confidence > b.confidence ? a : b,
    );
  }

  @override
  Widget build(BuildContext context) {
    final top = _topDetection;
    final info = top != null ? _diseaseData[top.classCode] : null;
    final isWide = MediaQuery.of(context).size.width > 700;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Resultado del Análisis'),
        centerTitle: true,
        backgroundColor: const Color(0xFF1565C0),
        foregroundColor: Colors.white,
      ),
      body: isWide
          ? _WideLayout(imageFile: imageFile, prediction: prediction, top: top, info: info)
          : _NarrowLayout(imageFile: imageFile, prediction: prediction, top: top, info: info),
    );
  }
}

// ── Wide layout (web / tablet) ────────────────────────────────────────────────

class _WideLayout extends StatelessWidget {
  final XFile imageFile;
  final PredictionResponse prediction;
  final Detection? top;
  final _DiseaseInfo? info;

  const _WideLayout({
    required this.imageFile,
    required this.prediction,
    required this.top,
    required this.info,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          flex: 5,
          child: _ImagePanel(imageFile: imageFile, prediction: prediction),
        ),
        Expanded(
          flex: 5,
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: _InfoPanel(prediction: prediction, top: top, info: info),
          ),
        ),
      ],
    );
  }
}

// ── Narrow layout (mobile) ────────────────────────────────────────────────────

class _NarrowLayout extends StatelessWidget {
  final XFile imageFile;
  final PredictionResponse prediction;
  final Detection? top;
  final _DiseaseInfo? info;

  const _NarrowLayout({
    required this.imageFile,
    required this.prediction,
    required this.top,
    required this.info,
  });

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _ImagePanel(imageFile: imageFile, prediction: prediction),
          const SizedBox(height: 16),
          _InfoPanel(prediction: prediction, top: top, info: info),
        ],
      ),
    );
  }
}

// ── Image panel ───────────────────────────────────────────────────────────────

class _ImagePanel extends StatelessWidget {
  final XFile imageFile;
  final PredictionResponse prediction;

  const _ImagePanel({required this.imageFile, required this.prediction});

  @override
  Widget build(BuildContext context) {
    final count = prediction.detections.length;
    return Container(
      color: Colors.black,
      constraints: BoxConstraints(
        minHeight: MediaQuery.of(context).size.height - kToolbarHeight,
      ),
      child: LayoutBuilder(
        builder: (context, constraints) {
          return Stack(
            alignment: Alignment.bottomLeft,
            children: [
              Center(
                child: Image.network(
                  imageFile.path,
                  fit: BoxFit.contain,
                  errorBuilder: (_, __, ___) => const Center(
                    child: Icon(Icons.broken_image, size: 80, color: Colors.white30),
                  ),
                ),
              ),
              if (prediction.detections.isNotEmpty)
                CustomPaint(
                  size: constraints.biggest,
                  painter: _BBoxPainter(
                    detections: prediction.detections,
                    imageWidth: prediction.imageWidth,
                    imageHeight: prediction.imageHeight,
                  ),
                ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                margin: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.black54,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  '$count detección(es)',
                  style: const TextStyle(color: Colors.white, fontSize: 13),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

// ── Bounding box painter ──────────────────────────────────────────────────────

class _BBoxPainter extends CustomPainter {
  final List<Detection> detections;
  final int imageWidth;
  final int imageHeight;

  const _BBoxPainter({
    required this.detections,
    required this.imageWidth,
    required this.imageHeight,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final scale = min(size.width / imageWidth, size.height / imageHeight);
    final offsetX = (size.width - imageWidth * scale) / 2;
    final offsetY = (size.height - imageHeight * scale) / 2;

    for (final det in detections) {
      final color = _diseaseData[det.classCode]?.riskColor ?? Colors.blue;
      final x1 = offsetX + det.bbox.x1 * scale;
      final y1 = offsetY + det.bbox.y1 * scale;
      final x2 = offsetX + det.bbox.x2 * scale;
      final y2 = offsetY + det.bbox.y2 * scale;

      // Box
      canvas.drawRect(
        Rect.fromLTRB(x1, y1, x2, y2),
        Paint()
          ..color = color
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2.5,
      );

      // Label background + text
      final label =
          '${det.classCode.toUpperCase()}  ${(det.confidence * 100).toStringAsFixed(0)}%';
      final tp = TextPainter(
        text: TextSpan(
          text: label,
          style: const TextStyle(
              color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold),
        ),
        textDirection: TextDirection.ltr,
      )..layout();

      final labelY = y1 - 18 < 0 ? y1 : y1 - 18;
      canvas.drawRect(
        Rect.fromLTWH(x1, labelY, tp.width + 8, 18),
        Paint()..color = color,
      );
      tp.paint(canvas, Offset(x1 + 4, labelY + 3));
    }
  }

  @override
  bool shouldRepaint(covariant _BBoxPainter old) =>
      old.detections != detections;
}

// ── Info panel ────────────────────────────────────────────────────────────────

class _InfoPanel extends StatelessWidget {
  final PredictionResponse prediction;
  final Detection? top;
  final _DiseaseInfo? info;

  const _InfoPanel({required this.prediction, required this.top, required this.info});

  @override
  Widget build(BuildContext context) {
    if (top == null) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(32),
          child: Text(
            'No se detectaron lesiones en la imagen.',
            style: TextStyle(fontSize: 16, color: Colors.grey),
          ),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const _SectionTitle('Diagnóstico principal'),
        const SizedBox(height: 10),
        _DiagnosisBadge(detection: top!, info: info),

        const SizedBox(height: 24),

        if (info != null) ...[
          const _SectionTitle('Sobre esta condición'),
          const SizedBox(height: 10),
          _InfoCard(
            icon: Icons.info_outline,
            color: const Color(0xFF1565C0),
            title: 'Descripción',
            body: info!.description,
          ),
          const SizedBox(height: 10),
          _InfoCard(
            icon: Icons.warning_amber_rounded,
            color: info!.riskColor,
            title: 'Nivel de riesgo: ${info!.risk}',
            body: info!.symptoms,
            bodyLabel: 'Síntomas',
          ),
          const SizedBox(height: 10),
          _InfoCard(
            icon: Icons.medical_services_outlined,
            color: Colors.teal,
            title: 'Recomendación',
            body: info!.recommendation,
          ),
          if (info!.isHighRisk) ...[
            const SizedBox(height: 12),
            _UrgentAppointmentButton(riskColor: info!.riskColor),
          ],
          const SizedBox(height: 24),
        ],

        if (prediction.detections.length > 1) ...[
          const _SectionTitle('Otras detecciones'),
          const SizedBox(height: 10),
          ...prediction.detections
              .where((d) => d != top)
              .map((d) => _SmallDetectionTile(detection: d)),
          const SizedBox(height: 16),
        ],

        const Text(
          'Este análisis es orientativo y no reemplaza el diagnóstico médico profesional.',
          style: TextStyle(fontSize: 11, color: Colors.grey, fontStyle: FontStyle.italic),
        ),
      ],
    );
  }
}

// ── Sub-widgets ───────────────────────────────────────────────────────────────

class _SectionTitle extends StatelessWidget {
  final String text;
  const _SectionTitle(this.text);

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
            color: const Color(0xFF1565C0),
          ),
    );
  }
}

class _DiagnosisBadge extends StatelessWidget {
  final Detection detection;
  final _DiseaseInfo? info;
  const _DiagnosisBadge({required this.detection, required this.info});

  @override
  Widget build(BuildContext context) {
    final conf = (detection.confidence * 100).toStringAsFixed(1);
    final riskColor = info?.riskColor ?? Colors.blueGrey;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: riskColor.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: riskColor, width: 1.5),
      ),
      child: Row(
        children: [
          CircleAvatar(
            radius: 28,
            backgroundColor: riskColor,
            child: Text(
              detection.classCode.toUpperCase().substring(0, 2),
              style: const TextStyle(
                  color: Colors.white, fontWeight: FontWeight.bold, fontSize: 14),
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  detection.className,
                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                Text(
                  'Código: ${detection.classCode.toUpperCase()}',
                  style: const TextStyle(color: Colors.grey, fontSize: 12),
                ),
                if (info != null)
                  Text(
                    'Riesgo: ${info!.risk}',
                    style: TextStyle(color: riskColor, fontWeight: FontWeight.w600),
                  ),
              ],
            ),
          ),
          Column(
            children: [
              Text(
                '$conf%',
                style: TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.bold,
                  color: riskColor,
                ),
              ),
              const Text('confianza', style: TextStyle(fontSize: 11, color: Colors.grey)),
            ],
          ),
        ],
      ),
    );
  }
}

class _InfoCard extends StatelessWidget {
  final IconData icon;
  final Color color;
  final String title;
  final String body;
  final String? bodyLabel;

  const _InfoCard({
    required this.icon,
    required this.color,
    required this.title,
    required this.body,
    this.bodyLabel,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(10),
        side: BorderSide(color: Colors.grey.shade200),
      ),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: color, size: 18),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    title,
                    style: TextStyle(fontWeight: FontWeight.w600, color: color),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            if (bodyLabel != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 4),
                child: Text(
                  bodyLabel!,
                  style: const TextStyle(
                      fontSize: 11, color: Colors.grey, fontWeight: FontWeight.w600),
                ),
              ),
            Text(body, style: const TextStyle(fontSize: 13, height: 1.5)),
          ],
        ),
      ),
    );
  }
}

class _UrgentAppointmentButton extends StatelessWidget {
  final Color riskColor;
  const _UrgentAppointmentButton({required this.riskColor});

  static const _sergasUrl = 'https://cita.sergas.es';

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      child: FilledButton.icon(
        style: FilledButton.styleFrom(
          backgroundColor: riskColor,
          padding: const EdgeInsets.symmetric(vertical: 14),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        ),
        icon: const Icon(Icons.calendar_month, color: Colors.white),
        label: const Text(
          'Pedir cita urgente en el SERGAS',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 15),
        ),
        onPressed: () async {
          final uri = Uri.parse(_sergasUrl);
          if (await canLaunchUrl(uri)) {
            await launchUrl(uri, mode: LaunchMode.externalApplication);
          }
        },
      ),
    );
  }
}

class _SmallDetectionTile extends StatelessWidget {
  final Detection detection;
  const _SmallDetectionTile({required this.detection});

  @override
  Widget build(BuildContext context) {
    return ListTile(
      dense: true,
      contentPadding: EdgeInsets.zero,
      leading: CircleAvatar(
        radius: 16,
        backgroundColor: Theme.of(context).colorScheme.primaryContainer,
        child: Text(
          detection.classCode.toUpperCase().substring(0, 2),
          style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold),
        ),
      ),
      title: Text(detection.className, style: const TextStyle(fontSize: 13)),
      trailing: Text(
        '${(detection.confidence * 100).toStringAsFixed(1)}%',
        style: TextStyle(
          fontWeight: FontWeight.bold,
          color: detection.confidence > 0.7 ? Colors.green : Colors.orange,
        ),
      ),
    );
  }
}
