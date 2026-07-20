import subprocess, sys

# Try several refs  
for ref in ['HEAD~15', 'HEAD~20']:
    r = subprocess.run(
        ['git', 'show', f'{ref}:clawai/desktop_server.py'],
        capture_output=True, text=True, cwd='D:\\ClawAI'
    )

with open('d:/clawi/git_show.txt', 'w') as out:
    if r.returncode == 0 and len(r.stdout) > 3000:
