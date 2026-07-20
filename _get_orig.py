import subprocess, sys

# Try several refs to find a version that has the original start_desktop code  
for ref in ['HEAD~15', 'HEAD~20']:
    r = subprocess.run(
        ['git', 'show', f'{ref}:clawai/desktop_server.py'],
        capture_output=True, text=True, cwd='D:\\ClawAI'
    )
    
with open('d:/clawi/git_show.txt', 'w') as f:
    if r.returncode == 0 and len(r.stdout) > 3000:
