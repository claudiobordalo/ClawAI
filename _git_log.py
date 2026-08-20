import subprocess, sys

# Check log first  
r = subprocess.run(
    ['git', 'log', '-15'],
    capture_output=True, text=True, cwd='D:\\ClawAI'
)
with open('d:/clawai/git_log.txt', 'w') as f:
    f.write(r.stdout[:2000])

# Try to get original desktop_server from git  
for ref in ['HEAD~15']:  # proper syntax without colon issue
    r = subprocess.run(
        ['git', 'show', f'{ref}:clawai/desktop_server.py'],
        capture_output=True, text=True, cwd='D:\\ClawAI'
    )

with open('d:/clawai/git_show.txt', 'w') as f:
    if r.returncode == 0 and len(r.stdout) > 3000:
        
        # Find the start_desktop function  
        lines = r.stdout.split('\n')
        in_start_desktop = False
        for i, l in enumerate(lines):
            if 'def start_desktop' in l:
                in_start_desktop = True
            
            if in_start_desktop:
                f.write(f'{i+1:>4d}: {l}\r\n')
