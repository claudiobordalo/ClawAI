import subprocess, sys, os.path as osp, json

results = {}

# Try git log  
r = subprocess.run(
    ['git', 'log', '--oneline', '-5'],
    capture_output=True, text=True, cwd='D:\\ClawAI'
)
results['git_log'] = {'returncode': r.returncode, 
                       'stdout_len': len(r.stdout), 
                       'stderr_len': len(r.stderr)}

# Try git show for desktop_server.py at various refs  
for ref in ['HEAD', 'HEAD~10']:
    pathspec = f'{ref}:clawai/desktop_server.py' if ':' in str(ref) else osp.join(ref, 'desktop_server.py')
    
with open('/tmp/git_results.json', 'w') as out:
