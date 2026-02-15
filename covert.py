#!/usr/bin/env python3
import subprocess
import json
import sys
import argparse
from datetime import datetime

# Colores para output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def log(message, color=RESET):
    print(f"{color}{message}{RESET}")

def run_command(command, shell=True, capture_output=True):
    try:
        result = subprocess.run(
            command, 
            shell=shell, 
            check=False, 
            stdout=subprocess.PIPE if capture_output else None, 
            stderr=subprocess.PIPE if capture_output else None,
            text=True
        )
        return result
    except Exception:
        return None

def check_tests():
    log("🧪 Ejecutando tests de seguridad...", YELLOW)
    # Ejecutamos un subconjunto rápido o todo según configuración
    # Excluimos E2E porque faltan binarios de Playwright en este entorno
    result = run_command("pytest --ignore=tests/e2e --ignore=soporte/tests/e2e", capture_output=False) 
    return result.returncode == 0

def get_outdated_packages():
    log("🔍 Buscando actualizaciones...", YELLOW)
    result = run_command("pip list --outdated --format=json")
    if result.returncode != 0:
        log("❌ Error al buscar actualizaciones", RED)
        return []
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        log("❌ Error al parsear JSON de pip", RED)
        return []

def backup_requirements():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"requirements_backup_{timestamp}.txt"
    log(f"💾 Creando backup en {filename}...", YELLOW)
    run_command(f"pip freeze > {filename}")
    return filename

def safe_update(pkg_name, current_ver, latest_ver, dry_run=False):
    log(f"\n📦 Procesando {pkg_name}: {current_ver} -> {latest_ver}", YELLOW)
    
    if dry_run:
        log("Skill: Modo Dry-Run (Simulación)", GREEN)
        return "SKIPPED"

    # 1. Update
    log(f"⬆️  Actualizando {pkg_name}...", YELLOW)
    update_res = run_command(f"pip install {pkg_name}=={latest_ver}")
    if update_res.returncode != 0:
        log(f"❌ Falló instalación de {pkg_name}", RED)
        return "FAILED_INSTALL"

    # 2. Verify
    if check_tests():
        log(f"✅ Tests pasaron. {pkg_name} actualizado exitosamente.", GREEN)
        return "UPDATED"
    else:
        log(f"❌ Tests fallaron. Iniciando Rollback de {pkg_name}...", RED)
        # 3. Rollback
        rollback_res = run_command(f"pip install {pkg_name}=={current_ver}")
        if rollback_res.returncode == 0:
            log(f"↩️  Rollback exitoso a {current_ver}. Sistema restaurado.", GREEN)
            return "ROLLED_BACK"
        else:
            log(f"💀 CRITICAL: Falló el rollback de {pkg_name}. Revisar manualmente.", RED)
            return "CRITICAL_FAILURE"

def main():
    parser = argparse.ArgumentParser(description="Safe Updater Tool")
    parser.add_argument("--dry-run", action="store_true", help="Simular sin instalar nada")
    parser.add_argument("--ignore", default=None, help="Lista de paquetes a ignorar separados por coma")
    args = parser.parse_args()

    ignored = args.ignore.split(",") if args.ignore else []

    log("🛡️  Iniciando Safe-Updater Protocol", GREEN)
    
    # Pre-check
    if not args.dry_run:
        if not check_tests():
            log("❌ El sistema ya tiene tests fallando. Abortando para no empeorar.", RED)
            sys.exit(1)
        backup_requirements()

    outdated = get_outdated_packages()
    if not outdated:
        log("✅ Todo está actualizado.", GREEN)
        return

    report = {"UPDATED": [], "ROLLED_BACK": [], "FAILED": [], "SKIPPED": []}

    for pkg in outdated:
        name = pkg['name']
        current = pkg['version']
        latest = pkg.get('latest_version') or pkg.get('latest')

        if name in ignored:
            log(f"⚠️  Ignorando {name} por configuración.", YELLOW)
            continue

        status = safe_update(name, current, latest, args.dry_run)
        
        if status == "UPDATED":
            report["UPDATED"].append(name)
        elif status == "ROLLED_BACK":
            report["ROLLED_BACK"].append(name)
        elif status == "SKIPPED":
            report["SKIPPED"].append(name)
        else:
            report["FAILED"].append(name)

    log("\n📊 Resumen Final:", GREEN)
    log(f"✅ Actualizados: {len(report['UPDATED'])} {report['UPDATED']}", GREEN)
    log(f"↩️  Revertidos:  {len(report['ROLLED_BACK'])} {report['ROLLED_BACK']}", RED)
    log(f"⚠️  Omitidos:    {len(report['SKIPPED'])} {report['SKIPPED']}", YELLOW)

if __name__ == "__main__":
    main()
