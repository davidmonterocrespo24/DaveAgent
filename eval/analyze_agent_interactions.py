#!/usr/bin/env python3
"""
Script para analizar las interacciones detalladas del agent.
Lee los logs JSON generados por el agent para cada tarea y genera
análisis de qué herramientas usó, qué archivos leyó, qué errores tuvo, etc.
"""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path


def find_json_logs(base_dir):
    """Busca todos los archivos JSON de logging del agent"""
    json_files = []

    # Buscar en .daveagent/logs/ o en el directorio base
    log_dirs = [
        Path(base_dir) / '.daveagent' / 'logs',
        Path(base_dir) / 'logs',
        Path(base_dir)
    ]

    for log_dir in log_dirs:
        if log_dir.exists():
            json_files.extend(log_dir.glob('*.json'))

    return json_files


def analyze_log_file(log_path):
    """Analiza un archivo de log JSON del agent"""
    try:
        with open(log_path, encoding='utf-8') as f:
            logs = [json.loads(line) for line in f if line.strip()]
    except Exception as e:
        print(f"   Warning: Could not read {log_path}: {e}")
        return None

    analysis = {
        'total_messages': len(logs),
        'tools_used': Counter(),
        'files_read': set(),
        'files_written': set(),
        'files_edited': set(),
        'errors': [],
        'thinking_events': 0,
        'tool_calls': 0,
        'duration_seconds': 0,
        'model_used': None
    }

    start_time = None
    end_time = None

    for log in logs:
        # Extract timestamp
        if 'timestamp' in log:
            ts = datetime.fromisoformat(log['timestamp'])
            if start_time is None:
                start_time = ts
            end_time = ts

        # Extract model info
        if 'model' in log and analysis['model_used'] is None:
            analysis['model_used'] = log['model']

        # Analyze message type
        msg_type = log.get('type', '')

        if msg_type == 'ThoughtEvent':
            analysis['thinking_events'] += 1

        elif msg_type == 'ToolCallRequestEvent':
            analysis['tool_calls'] += 1
            # Extract tool names
            content = log.get('content', {})
            if isinstance(content, dict):
                tool_name = content.get('name', '')
                if tool_name:
                    analysis['tools_used'][tool_name] += 1

                    # Extract file operations
                    args = content.get('arguments', {})
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except:
                            args = {}

                    if tool_name == 'read_file':
                        file_path = args.get('target_file', '')
                        if file_path:
                            analysis['files_read'].add(file_path)

                    elif tool_name == 'write_file':
                        file_path = args.get('target_file', '')
                        if file_path:
                            analysis['files_written'].add(file_path)

                    elif tool_name == 'edit_file':
                        file_path = args.get('target_file', '')
                        if file_path:
                            analysis['files_edited'].add(file_path)

        elif msg_type == 'ToolCallExecutionEvent':
            # Check for errors
            content = log.get('content', {})
            if isinstance(content, dict):
                is_error = content.get('is_error', False)
                if is_error:
                    error_msg = content.get('content', '')
                    analysis['errors'].append(error_msg)

    # Calculate duration
    if start_time and end_time:
        analysis['duration_seconds'] = (end_time - start_time).total_seconds()

    # Convert sets to lists for JSON serialization
    analysis['files_read'] = list(analysis['files_read'])
    analysis['files_written'] = list(analysis['files_written'])
    analysis['files_edited'] = list(analysis['files_edited'])

    return analysis


def generate_interaction_report(analyses, output_path):
    """Genera un reporte HTML de las interacciones del agent"""

    total_tasks = len(analyses)

    # Agregar estadísticas globales
    all_tools = Counter()
    total_messages = 0
    total_tool_calls = 0
    total_thinking = 0
    total_errors = 0

    for analysis in analyses.values():
        if analysis:
            all_tools.update(analysis['tools_used'])
            total_messages += analysis['total_messages']
            total_tool_calls += analysis['tool_calls']
            total_thinking += analysis['thinking_events']
            total_errors += len(analysis['errors'])

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Análisis de Interacciones del agent - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary-number {{
            font-size: 32px;
            font-weight: bold;
            color: #f5576c;
        }}
        .summary-label {{
            color: #666;
            font-size: 14px;
            margin-top: 5px;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .tool-bar {{
            display: flex;
            align-items: center;
            margin: 10px 0;
        }}
        .tool-name {{
            width: 150px;
            font-weight: 500;
        }}
        .tool-bar-fill {{
            height: 30px;
            background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
            border-radius: 5px;
            display: flex;
            align-items: center;
            padding: 0 10px;
            color: white;
            font-weight: bold;
        }}
        .task-details {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .task-header {{
            font-size: 18px;
            font-weight: bold;
            color: #333;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }}
        .metric-row {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }}
        .metric {{
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
        }}
        .metric-label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }}
        .metric-value {{
            font-size: 20px;
            font-weight: bold;
            color: #333;
            margin-top: 5px;
        }}
        .file-list {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            max-height: 200px;
            overflow-y: auto;
        }}
        .file-item {{
            padding: 5px 0;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        }}
        .error-box {{
            background: #f8d7da;
            border-left: 4px solid #dc3545;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }}
        .error-text {{
            color: #721c24;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 Análisis de Interacciones del agent</h1>
        <p>Reporte generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="summary">
        <div class="summary-card">
            <div class="summary-number">{total_tasks}</div>
            <div class="summary-label">Tareas Analizadas</div>
        </div>
        <div class="summary-card">
            <div class="summary-number">{total_messages}</div>
            <div class="summary-label">Total de Mensajes</div>
        </div>
        <div class="summary-card">
            <div class="summary-number">{total_tool_calls}</div>
            <div class="summary-label">Llamadas a Herramientas</div>
        </div>
        <div class="summary-card">
            <div class="summary-number">{total_thinking}</div>
            <div class="summary-label">Eventos de Pensamiento</div>
        </div>
        <div class="summary-card">
            <div class="summary-number">{total_errors}</div>
            <div class="summary-label">Errores Encontrados</div>
        </div>
        <div class="summary-card">
            <div class="summary-number">{total_messages / total_tasks if total_tasks > 0 else 0:.1f}</div>
            <div class="summary-label">Mensajes Promedio/Tarea</div>
        </div>
    </div>

    <div class="chart-container">
        <h2>📊 Herramientas Más Utilizadas</h2>
"""

    # Top 10 herramientas
    max_count = max(all_tools.values()) if all_tools else 1
    for tool, count in all_tools.most_common(10):
        width = (count / max_count) * 100
        html += f"""
        <div class="tool-bar">
            <div class="tool-name">{tool}</div>
            <div class="tool-bar-fill" style="width: {width}%;">
                {count}
            </div>
        </div>
"""

    html += """
    </div>

    <h2 style="margin-top: 30px; margin-bottom: 20px;">📝 Detalle por Tarea</h2>
"""

    # Detalles de cada tarea
    for task_id, analysis in sorted(analyses.items()):
        if not analysis:
            continue

        html += f"""
    <div class="task-details">
        <div class="task-header">{task_id}</div>

        <div class="metric-row">
            <div class="metric">
                <div class="metric-label">Mensajes Totales</div>
                <div class="metric-value">{analysis['total_messages']}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Llamadas a Herramientas</div>
                <div class="metric-value">{analysis['tool_calls']}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Eventos de Pensamiento</div>
                <div class="metric-value">{analysis['thinking_events']}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Duración</div>
                <div class="metric-value">{analysis['duration_seconds']:.1f}s</div>
            </div>
        </div>
"""

        # Archivos leídos
        if analysis['files_read']:
            html += f"""
        <h4>📖 Archivos Leídos ({len(analysis['files_read'])})</h4>
        <div class="file-list">
"""
            for file in sorted(analysis['files_read']):
                html += f'            <div class="file-item">{file}</div>\n'
            html += """
        </div>
"""

        # Archivos editados
        if analysis['files_edited']:
            html += f"""
        <h4>✏️ Archivos Editados ({len(analysis['files_edited'])})</h4>
        <div class="file-list">
"""
            for file in sorted(analysis['files_edited']):
                html += f'            <div class="file-item">{file}</div>\n'
            html += """
        </div>
"""

        # Archivos escritos
        if analysis['files_written']:
            html += f"""
        <h4>📝 Archivos Escritos ({len(analysis['files_written'])})</h4>
        <div class="file-list">
"""
            for file in sorted(analysis['files_written']):
                html += f'            <div class="file-item">{file}</div>\n'
            html += """
        </div>
"""

        # Errores
        if analysis['errors']:
            html += f"""
        <h4>⚠️ Errores ({len(analysis['errors'])})</h4>
"""
            for error in analysis['errors']:
                error_escaped = error.replace('<', '&lt;').replace('>', '&gt;')
                html += f"""
        <div class="error-box">
            <div class="error-text">{error_escaped}</div>
        </div>
"""

        html += """
    </div>
"""

    html += """
</body>
</html>
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✓ Reporte de interacciones generado: {output_path}")


def main():
    """Función principal"""
    print("=" * 70)
    print("  Analizador de Interacciones del agent")
    print("=" * 70)
    print()

    base_dir = Path(__file__).parent.parent

    print("🔍 Buscando archivos de log del agent...")
    log_files = find_json_logs(base_dir)

    if not log_files:
        print("⚠️  No se encontraron archivos de log JSON")
        print("   Verifica que el agent esté configurado para generar logs JSON")
        return

    print(f"   Encontrados {len(log_files)} archivo(s) de log")
    print()

    print("📊 Analizando logs...")
    analyses = {}

    for log_file in log_files:
        # Intentar extraer el instance_id del nombre del archivo
        instance_id = log_file.stem
        print(f"   - Analizando {instance_id}...")

        analysis = analyze_log_file(log_file)
        if analysis:
            analyses[instance_id] = analysis

    print()
    print(f"✓ Análisis completado: {len(analyses)} tareas")
    print()

    # Generar reporte
    print("📝 Generando reporte HTML...")
    output_path = base_dir / 'eval' / f'interacciones_agent_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'
    generate_interaction_report(analyses, output_path)

    print()
    print("=" * 70)
    print("✅ Análisis completado!")
    print("=" * 70)
    print(f"\n📄 Reporte: {output_path}")
    print()


if __name__ == '__main__':
    main()
