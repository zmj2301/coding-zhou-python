#!/usr/bin/env python3
import sys
import os
import json

with open('/tmp/llama_server_args.log', 'a') as f:
    f.write('ARGS: ' + json.dumps(sys.argv[1:]) + '\n')

if '--list-devices' in sys.argv:
    print('{"version":"1.0","capabilities":["cpu"],"devices":[{"library":"cpu","driver":"cpu","name":"cpu","total_mem":0,"free_mem":0}]}')
    sys.exit(0)

SKIP_BOOL = {'--no-webui', '--offline', '--no-mmap', '--mmap',
             '--verbose-prompt', '--no-log-prefix', '--no-log-timestamps',
             '--no-jinja', '--context-shift', '--verbose'}

SKIP_VALUE = {'--flash-attn', '--keep', '--n-predict', '--gpu-layers', '--main-gpu',
              '--log-verbosity', '--chat-template', '--load-mode', '-ub', '-np'}

filtered = []
i = 0
args = sys.argv[1:]
while i < len(args):
    arg = args[i]
    if arg in SKIP_BOOL:
        i += 1
        continue
    if arg in SKIP_VALUE:
        if i + 1 < len(args):
            i += 2
        else:
            i += 1
        continue
    filtered.append(arg)
    i += 1

with open('/tmp/llama_server_filtered.log', 'a') as f:
    f.write('FILTERED: ' + json.dumps(filtered) + '\n')

os.execv('/usr/local/lib/ollama/llama-server.real', ['llama-server'] + filtered)
