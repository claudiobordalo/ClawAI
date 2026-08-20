import subprocess as sp, json, os.path as osp

results = {}

base_dir = 'D:\\\\ClawAI'  # double escape for Windows path in Python string inside file  
r_log = sp.run(['git', 'log', '--oneline', '-5'], capture_output=True, text=True, cwd=base_dir)
results['git_log_rc'] = r_log.returncode
results['git_log_stdout_len'] = len(r_log.stdout)

# Try git show at various refs  
for ref in ['HEAD']:  # start with current HEAD since we already know the file exists there
    pathspec = f'{ref}:clawai/desktop_server.py' if ':' not in str(ref) else None
    
with open(osp.join(base_dir, '_git_results.json'), 'w') as f:
