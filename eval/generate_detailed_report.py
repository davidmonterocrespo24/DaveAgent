#!/usr/bin/env python3
"""
Script para generar un reporte detallado de la evaluación SWE-bench.
Analiza predictions.jsonl, el reporte de evaluación, y genera un informe completo
con las interacciones del agente, código generado vs esperado, y análisis de fallos.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import difflib

def load_predictions(predictions_path):
    """Carga las predicciones del agente"""
    predictions = []
    if not os.path.exists(predictions_path):
        print(f"Warning: {predictions_path} not found")
        return predictions

    with open(predictions_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                predictions.append(json.loads(line))
    return predictions

def load_evaluation_report(report_path):
    """Carga el reporte de evaluación de SWE-bench"""
    if not os.path.exists(report_path):
        print(f"Warning: {report_path} not found")
        return {}

    with open(report_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_dataset_instances(dataset_path=None):
    """Carga las instancias del dataset para obtener info adicional"""
    # Por ahora retornamos dict vacío, se puede extender para cargar el dataset completo
    return {}

def analyze_patch(patch_text):
    """Analiza un patch y extrae estadísticas"""
    if not patch_text or not patch_text.strip():
        return {
            'empty': True,
            'files_changed': 0,
            'lines_added': 0,
            'lines_removed': 0,
            'total_changes': 0
        }

    lines = patch_text.split('\n')
    files_changed = set()
    lines_added = 0
    lines_removed = 0

    for line in lines:
        if line.startswith('diff --git'):
            # Extract filename
            parts = line.split()
            if len(parts) >= 3:
                files_changed.add(parts[2])
        elif line.startswith('+') and not line.startswith('+++'):
            lines_added += 1
        elif line.startswith('-') and not line.startswith('---'):
            lines_removed += 1

    return {
        'empty': False,
        'files_changed': len(files_changed),
        'files': list(files_changed),
        'lines_added': lines_added,
        'lines_removed': lines_removed,
        'total_changes': lines_added + lines_removed
    }

def categorize_failure(instance_id, prediction, eval_result):
    """Categoriza el tipo de fallo"""
    patch = prediction.get('model_patch', '')

    if not patch or not patch.strip():
        return 'NO_PATCH', 'El agente no generó ningún patch'

    if eval_result is None:
        return 'NOT_EVALUATED', 'No se evaluó (posiblemente error de infraestructura)'

    # Aquí se puede extender con más categorías basadas en el eval_result
    if eval_result.get('resolved', False):
        return 'SUCCESS', 'Tarea resuelta correctamente'

    return 'PATCH_INCORRECT', 'Patch generado pero no pasó los tests'

def generate_html_report(predictions, eval_report, output_path):
    """Genera un reporte HTML detallado"""

    # Estadísticas globales
    total_tasks = len(predictions)
    tasks_with_patches = sum(1 for p in predictions if p.get('model_patch', '').strip())

    # Categorizar resultados
    resolved = eval_report.get('resolved_ids', eval_report.get('resolved', [])) if isinstance(eval_report, dict) else []
    resolved_ids = set(resolved) if isinstance(resolved, list) else set()

    categorized = defaultdict(list)
    for pred in predictions:
        instance_id = pred['instance_id']
        is_resolved = instance_id in resolved_ids

        if is_resolved:
            category = 'SUCCESS'
        elif not pred.get('model_patch', '').strip():
            category = 'NO_PATCH'
        else:
            category = 'PATCH_INCORRECT'

        categorized[category].append(pred)

    # Generar HTML
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte Detallado SWE-bench - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .stat-number {{
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }}
        .stat-label {{
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
        }}
        .category {{
            background: white;
            margin-bottom: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .category-header {{
            padding: 20px;
            font-size: 20px;
            font-weight: bold;
            border-bottom: 2px solid #f0f0f0;
        }}
        .category-header.success {{ background: #d4edda; color: #155724; }}
        .category-header.failed {{ background: #f8d7da; color: #721c24; }}
        .category-header.no-patch {{ background: #fff3cd; color: #856404; }}

        .task {{
            border-bottom: 1px solid #f0f0f0;
            padding: 20px;
        }}
        .task:last-child {{ border-bottom: none; }}

        .task-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        .task-id {{
            font-weight: bold;
            color: #333;
            font-size: 16px;
        }}
        .task-status {{
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
        }}
        .status-success {{ background: #28a745; color: white; }}
        .status-failed {{ background: #dc3545; color: white; }}
        .status-no-patch {{ background: #ffc107; color: #333; }}

        .problem-statement {{
            background: #f8f9fa;
            padding: 15px;
            border-left: 4px solid #667eea;
            margin: 15px 0;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            overflow-x: auto;
            max-height: 200px;
            overflow-y: auto;
        }}
        .patch {{
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            overflow-x: auto;
            max-height: 400px;
            overflow-y: auto;
        }}
        .patch-empty {{
            background: #fff3cd;
            color: #856404;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
            text-align: center;
            font-style: italic;
        }}
        .patch-stats {{
            display: flex;
            gap: 20px;
            margin: 10px 0;
            font-size: 13px;
        }}
        .patch-stat {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .added {{ color: #28a745; }}
        .removed {{ color: #dc3545; }}
        .toggle-btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 13px;
            margin-top: 10px;
        }}
        .toggle-btn:hover {{
            background: #5568d3;
        }}
        .hidden {{
            display: none;
        }}
        pre {{
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .metric-bar {{
            height: 20px;
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .metric-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s ease;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Reporte Detallado de Evaluación SWE-bench</h1>
        <p>Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="stats">
        <div class="stat-card">
            <div class="stat-label">Total de Tareas</div>
            <div class="stat-number">{total_tasks}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Patches Generados</div>
            <div class="stat-number">{tasks_with_patches}</div>
            <div class="metric-bar">
                <div class="metric-fill" style="width: {tasks_with_patches/total_tasks*100:.1f}%"></div>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Resueltas Correctamente</div>
            <div class="stat-number" style="color: #28a745;">{len(categorized['SUCCESS'])}</div>
            <div class="metric-bar">
                <div class="metric-fill" style="width: {len(categorized['SUCCESS'])/total_tasks*100:.1f}%; background: #28a745;"></div>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Tasa de Éxito</div>
            <div class="stat-number">{len(categorized['SUCCESS'])/total_tasks*100:.1f}%</div>
        </div>
    </div>
"""

    # Sección de tareas exitosas
    if categorized['SUCCESS']:
        html += f"""
    <div class="category">
        <div class="category-header success">
            ✅ Tareas Resueltas Correctamente ({len(categorized['SUCCESS'])})
        </div>
"""
        for pred in categorized['SUCCESS']:
            patch_analysis = analyze_patch(pred.get('model_patch', ''))
            html += generate_task_html(pred, 'success', patch_analysis)
        html += "    </div>\n"

    # Sección de tareas con patch incorrecto
    if categorized['PATCH_INCORRECT']:
        html += f"""
    <div class="category">
        <div class="category-header failed">
            ❌ Patches Generados pero Incorrectos ({len(categorized['PATCH_INCORRECT'])})
        </div>
"""
        for pred in categorized['PATCH_INCORRECT']:
            patch_analysis = analyze_patch(pred.get('model_patch', ''))
            html += generate_task_html(pred, 'failed', patch_analysis)
        html += "    </div>\n"

    # Sección de tareas sin patch
    if categorized['NO_PATCH']:
        html += f"""
    <div class="category">
        <div class="category-header no-patch">
            ⚠️ Tareas sin Patch Generado ({len(categorized['NO_PATCH'])})
        </div>
"""
        for pred in categorized['NO_PATCH']:
            patch_analysis = analyze_patch(pred.get('model_patch', ''))
            html += generate_task_html(pred, 'no-patch', patch_analysis)
        html += "    </div>\n"

    html += """
    <script>
        function togglePatch(id) {
            const element = document.getElementById(id);
            element.classList.toggle('hidden');
            const btn = document.querySelector(`[onclick="togglePatch('${id}')"]`);
            btn.textContent = element.classList.contains('hidden') ? 'Mostrar Patch' : 'Ocultar Patch';
        }
    </script>
</body>
</html>
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✓ Reporte HTML generado: {output_path}")

def generate_task_html(pred, status, patch_analysis):
    """Genera el HTML para una tarea individual"""
    instance_id = pred['instance_id']
    patch = pred.get('model_patch', '')

    status_class = f"status-{status}"
    status_text = {
        'success': 'RESUELTO ✓',
        'failed': 'INCORRECTO ✗',
        'no-patch': 'SIN PATCH'
    }.get(status, 'DESCONOCIDO')

    html = f"""
        <div class="task">
            <div class="task-header">
                <div class="task-id">{instance_id}</div>
                <div class="task-status {status_class}">{status_text}</div>
            </div>
"""

    # Estadísticas del patch si existe
    if not patch_analysis['empty']:
        html += f"""
            <div class="patch-stats">
                <div class="patch-stat">
                    📁 <strong>{patch_analysis['files_changed']}</strong> archivo(s) modificado(s)
                </div>
                <div class="patch-stat added">
                    + <strong>{patch_analysis['lines_added']}</strong> líneas
                </div>
                <div class="patch-stat removed">
                    - <strong>{patch_analysis['lines_removed']}</strong> líneas
                </div>
            </div>
"""
        if patch_analysis['files']:
            html += f"""
            <div style="font-size: 12px; color: #666; margin: 5px 0;">
                Archivos: {', '.join(patch_analysis['files'])}
            </div>
"""

    # Patch generado
    patch_id = f"patch-{instance_id.replace('__', '-').replace('_', '-')}"
    if patch and patch.strip():
        # Escape HTML characters
        patch_escaped = patch.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        html += f"""
            <button class="toggle-btn" onclick="togglePatch('{patch_id}')">Mostrar Patch</button>
            <div id="{patch_id}" class="patch hidden">
                <pre>{patch_escaped}</pre>
            </div>
"""
    else:
        html += """
            <div class="patch-empty">
                ⚠️ No se generó ningún patch para esta tarea
            </div>
"""

    html += "        </div>\n"
    return html

def generate_markdown_report(predictions, eval_report, output_path):
    """Genera un reporte en formato Markdown"""

    total_tasks = len(predictions)
    tasks_with_patches = sum(1 for p in predictions if p.get('model_patch', '').strip())

    resolved = eval_report.get('resolved_ids', eval_report.get('resolved', [])) if isinstance(eval_report, dict) else []
    resolved_ids = set(resolved) if isinstance(resolved, list) else set()

    md = f"""# 📊 Reporte Detallado de Evaluación SWE-bench

**Generado**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Resumen Ejecutivo

| Métrica | Valor | Porcentaje |
|---------|-------|------------|
| Total de Tareas | {total_tasks} | 100% |
| Patches Generados | {tasks_with_patches} | {tasks_with_patches/total_tasks*100:.1f}% |
| Resueltas Correctamente | {len(resolved_ids)} | {len(resolved_ids)/total_tasks*100:.1f}% |
| Con Patch Incorrecto | {tasks_with_patches - len(resolved_ids)} | {(tasks_with_patches - len(resolved_ids))/total_tasks*100:.1f}% |
| Sin Patch | {total_tasks - tasks_with_patches} | {(total_tasks - tasks_with_patches)/total_tasks*100:.1f}% |

---

"""

    # Análisis detallado de cada tarea
    for i, pred in enumerate(predictions, 1):
        instance_id = pred['instance_id']
        patch = pred.get('model_patch', '')
        is_resolved = instance_id in resolved_ids

        status_emoji = "✅" if is_resolved else ("❌" if patch.strip() else "⚠️")
        status_text = "RESUELTO" if is_resolved else ("INCORRECTO" if patch.strip() else "SIN PATCH")

        md += f"""## {i}. {status_emoji} {instance_id}

**Estado**: {status_text}

"""

        patch_analysis = analyze_patch(patch)
        if not patch_analysis['empty']:
            md += f"""### Estadísticas del Patch
- **Archivos modificados**: {patch_analysis['files_changed']}
- **Líneas agregadas**: {patch_analysis['lines_added']}
- **Líneas eliminadas**: {patch_analysis['lines_removed']}
- **Cambios totales**: {patch_analysis['total_changes']}

"""
            if patch_analysis['files']:
                md += f"**Archivos**: `{'`, `'.join(patch_analysis['files'])}`\n\n"

        if patch and patch.strip():
            md += f"""### Patch Generado

```diff
{patch}
```

"""
        else:
            md += "### ⚠️ No se generó ningún patch\n\n"

        md += "---\n\n"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md)

    print(f"✓ Reporte Markdown generado: {output_path}")

def main():
    """Función principal"""
    print("="*70)
    print("  Generador de Reporte Detallado SWE-bench")
    print("="*70)
    print()

    # Rutas
    base_dir = Path(__file__).parent
    predictions_path = base_dir / 'predictions.jsonl'
    report_path = base_dir / 'CodeAgent-v1.evaluacion_prueba_v1.json'

    # Cargar datos
    print("📥 Cargando datos...")
    predictions = load_predictions(predictions_path)
    eval_report = load_evaluation_report(report_path)

    print(f"   - Predicciones cargadas: {len(predictions)}")
    print(f"   - Reporte de evaluación: {'✓' if eval_report else '✗'}")
    print()

    # Generar reportes
    print("📝 Generando reportes...")

    # Reporte HTML
    html_output = base_dir / f'reporte_detallado_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
    generate_html_report(predictions, eval_report, html_output)

    # Reporte Markdown
    md_output = base_dir / f'reporte_detallado_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
    generate_markdown_report(predictions, eval_report, md_output)

    print()
    print("="*70)
    print("✅ Reportes generados exitosamente!")
    print("="*70)
    print(f"\n📄 HTML: {html_output}")
    print(f"📄 Markdown: {md_output}")
    print()

if __name__ == '__main__':
    main()
