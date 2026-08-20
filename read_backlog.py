import json  
with open('D:/ClawAI/clawai/growth_backlog.json', 'r') as f:  
    data = json.load(f)  
    print(len(data))  
    for t in data[:5]: print(t.get('id'), t.get('title')) 
