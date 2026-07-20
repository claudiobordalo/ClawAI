import subprocess, sys

# Check what HEAD~15 resolves to
r = subprocess.run(
    ['git', 'rev-parse', '--verify', 'HEAD~15'],
    capture_output=True, text=True, cwd='D:\\ClawAI'
)
print(f'rev-parse result: returncode={r.returncode}, stdout={repr(r.stdout[:200])}')

# Try the show command with explicit pathspec approach  
for ref in ['HEAD~15']:
    r = subprocess.run(
        ['git', 'show', f'{ref}:clawai/desktop_server.py'],
        capture_output=True, text=True, cwd='D:\\ClawAI'
    )

with open('d:/clawi/git_show.txt', 'w') as out:
    if r.returncode == 0 and len(r.stdout) > 3000:
