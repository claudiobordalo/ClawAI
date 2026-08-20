import subprocess, sys, os

# Try several refs  
for ref in ['HEAD~15', 'HEAD~20']:
    r = subprocess.run(
        ['git', 'show', f'{ref}:clawai/desktop_server.py'],
        capture_output=True, text=True, cwd='D:\\ClawAI'
    )

out_path = os.path.join(os.environ['USERPROFILE'] or '.', '_orig_desktop.txt')
with open(out_path, 'w') as out:
    if r.returncode == 0 and len(r.stdout) > 3000:
        
        lines = r.stdout.split('\n')
        in_start_desktop = False
        for i, l in enumerate(lines):
            if 'def start_desktop' in l:
                print(f"Found at line {i+1}")
                sys.stderr.write("FOUND\n")
                in_start_desktop = True
            
            if in_start_desktop:
                out.write(l + '\n')
