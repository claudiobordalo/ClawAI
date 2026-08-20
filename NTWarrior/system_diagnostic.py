import os
import platform
import psutil
import datetime
import json

def get_system_snapshot():
    snapshot = {}
    
    # 1. Informações de Sistema Básico
    snapshot['os'] = platform.system()
    snapshot['os_release'] = platform.release()
    snapshot['cpu_count'] = psutil.cpu_count()
    
    # 2. Uso de Recursos
    snapshot['cpu_usage'] = psutil.cpu_percent(interval=1)
    snapshot['memory'] = psutil.virtual_memory()._asdict()
    snapshot['disk'] = psutil.disk_usage('/')._asdict()
    
    # 3. Detecção de Ameaças (Critérios de Anomalia)
    suspicious_processes = []
    # Lista simples de palavras-chave suspeitas (Simulação de Banco de Dados de Vírus)
    threat_keywords = ['miner', 'trojan', 'malware', 'shell', 'nc.exe', 'powershell.exe']
    
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'exe']):
        try:
            # Critério 1: Uso de CPU muito alto (> 80%)
            # Critério 2: Nome do processo contém palavras-chave de ameaça
            # Critério 3: Processo sem caminho de executável definido (comum em alguns malwares)
            
            p_name = proc.info['name'].lower()
            is_suspicious = False
            reason = ""

            if proc.info['cpu_percent'] > 80.0:
                is_suspicious = True
                reason = "High CPU Usage"
            
            if any(kw in p_name for kw in threat_keywords):
                is_suspicious = True
                reason = "Threat Keyword Match"

            if not proc.info.get('exe') and p_name != "" and proc.info['cpu_percent'] > 10.0:
                is_suspicious = True
                reason = "No Executable Path"

            if is_suspicious:
                suspicious_processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cpu': proc.info['cpu_percent'],
                    'mem': proc.info['memory_percent'],
                    'reason': reason
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
            
    snapshot['suspicious_processes'] = suspicious_processes
    snapshot['threat_level'] = "LOW"
    
    # Definir nível de ameaça baseado na quantidade de processos suspeitos
    if len(suspicious_processes) > 0:
        snapshot['threat_level'] = "MEDIUM" if len(suspicious_processes) < 3 else "HIGH"
    
    # 4. Conexões de Rede Ativas
    snapshot['net_connections'] = len(psutil.net_connections())
    
    return snapshot

if __name__ == "__main__":
    data = get_system_snapshot()
    # Saída em JSON para facilitar a leitura pela IA
    print(json.dumps(data, indent=2))
