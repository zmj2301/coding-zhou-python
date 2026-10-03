#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从阿里云 ECS 侧执行 Cloudflare Worker 部署（绕过本机代理链路故障）

背景
----
本机到 api.cloudflare.com 的链路在某些代理节点下完全不通（站点域名与 GitHub
却可达），导致 `wrangler deploy` 连续数十次失败。ECS（39.107.96.165）出网正常，
因此把「构建 + 部署」整体搬到服务器上执行。

前置条件
--------
1. ECS 已安装 node / wrangler（实测 node v22.23.2、wrangler 4.12.0）
2. ECS 能访问 github.com 与 api.cloudflare.com
3. ECS 上已有 wrangler OAuth 凭据：本脚本会自动从本机
   %APPDATA%/xdg.config/.wrangler/config/default.toml 上传（token 过期时
   wrangler 会用refresh_token 自动续期，无需人工干预）

用法
----
    python _deploy_from_ecs.py            # 常规：克隆 → 构建 → 部署
    python _deploy_from_ecs.py --keep     # 复用已克隆的代码目录，跳过 git clone

注意
----
- 部署目录用 /root/cf-deploy/repo，与线上业务目录 /home/code-explorer 隔离，
  不会影响正在运行的 ecs-server.py
- 部署成功后需清 KV 的 cache: 前缀缓存；实测目前该前缀为空（可选步骤已内置）
"""

import os
import sys
import uuid

import paramiko

HOST = '39.107.96.165'
USER = 'root'
PWD = os.environ.get('ECS_PASSWORD', 'ZHOUmj328425108*')

DEPLOY_DIR = '/root/cf-deploy'
REPO_DIR = f'{DEPLOY_DIR}/repo'
REPO_URL = 'https://github.com/zmj2301/coding-zhou-python.git'

LOCAL_WRANGLER_CFG = os.path.join(
    os.environ.get('APPDATA', ''), 'xdg.config', '.wrangler', 'config', 'default.toml'
)
REMOTE_WRANGLER_CFG = '/root/.config/.wrangler/config/default.toml'

CF_ACCOUNT = 'd6b8ca32610afe0fd9407736b9266cb3'
CF_KV_NS = '69c61f369a764a519631b00e613f7ea6'


def run(ssh, cmd, timeout=1800, tail=80):
    """执行远程命令并打印输出。"""
    print(f'\n$ {cmd[:120]}')
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', 'replace')
    err = stderr.read().decode('utf-8', 'replace')
    lines = out.splitlines()
    print('\n'.join(lines[-tail:]) if tail and len(lines) > tail else out)
    if err.strip():
        print('[STDERR]', err.strip()[:1500])
    return out, err


def upload_credential(ssh):
    """把本机 wrangler OAuth 凭据推到 ECS。"""
    if not os.path.exists(LOCAL_WRANGLER_CFG):
        print(f'[warn] 本机未找到 {LOCAL_WRANGLER_CFG}，跳过凭据上传')
        return
    cfg = open(LOCAL_WRANGLER_CFG, 'r', encoding='utf-8').read()
    sftp = ssh.open_sftp()
    try:
        sftp.mkdir('/root/.config/.wrangler/config')
    except Exception:
        pass
    with sftp.open(REMOTE_WRANGLER_CFG, 'w') as f:
        f.write(cfg)
    sftp.close()
    print('[ok] wrangler 凭据已上传（过期会自动续期）')


def main():
    keep = '--keep' in sys.argv

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, port=22, username=USER, password=PWD, timeout=20)
    try:
        upload_credential(ssh)

        # 1) 确认认证（whoami 会触发 token 刷新）
        out, _ = run(ssh, 'cd /root && timeout 120 wrangler whoami 2>&1 | head -8', timeout=200)
        if 'not authenticated' in out:
            print('[fail] wrangler 仍未认证，终止')
            return 1

        # 2) 拉代码
        if keep:
            run(ssh, f'cd {REPO_DIR} && git pull --depth 1 origin main 2>&1 | tail -5')
        else:
            run(ssh, f'rm -rf {REPO_DIR} && mkdir -p {DEPLOY_DIR} && '
                     f'cd {DEPLOY_DIR} && timeout 900 git clone --depth 1 {REPO_URL} repo 2>&1 | tail -3')
        run(ssh, f'cd {REPO_DIR} && git log --oneline -1')

        # 3) 校验关键代码标记（防止推到旧版本）
        run(ssh, f"cd {REPO_DIR} && echo -n 'officePreviewPage=' && grep -c officePreviewPage code-explorer/worker.ts; "
                 f"echo -n 'upload/toggle=' && grep -c 'api/upload/toggle' code-explorer/worker.ts; "
                 f"diff -q index.html code-explorer/index.html && echo INDEX_IDENTICAL")

        # 4) 构建
        out, _ = run(ssh, f'cd {REPO_DIR} && timeout 900 python3 build.py 2>&1 | tail -6', timeout=1200)
        if '构建完成' not in out:
            print('[fail] 构建未完成，终止部署')
            return 1
        run(ssh, f'cd {REPO_DIR} && diff -q public/index.html index.html && echo ASSETS_OK')

        # 5) 部署
        out, _ = run(ssh, f'cd {REPO_DIR} && CI=1 timeout 900 wrangler deploy 2>&1 | tail -25', tail=40)
        if 'Success!' not in out and 'Current Version ID' not in out:
            print('[fail] 部署失败')
            return 1

        # 6) 清 KV cache: 前缀（可选）
        py = (
            "import json,urllib.request\n"
            "tok=[l for l in open('/root/.config/.wrangler/config/default.toml') "
            "if l.startswith('oauth_token')][0].split('\"')[1]\n"
            f"base='https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT}"
            f"/storage/kv/namespaces/{CF_KV_NS}'\n"
            "h={'Authorization':'Bearer '+tok}\n"
            "ks=json.load(urllib.request.urlopen(urllib.request.Request(base+'/keys?limit=1000',"
            "headers=h)))['result']\n"
            "tgt=[k['name'] for k in ks if k['name'].startswith('cache:')]\n"
            "print('cache keys:',len(tgt))\n"
            "for k in tgt:\n"
            "    urllib.request.urlopen(urllib.request.Request(base+'/values/'+k,headers=h,"
            "method='DELETE'))\n"
            "print('cleared',len(tgt))\n"
        )
        run(ssh, "python3 - <<'PYEOF'\n" + py + "\nPYEOF", timeout=300)

        print('\n[OK] 部署完成')
        return 0
    finally:
        ssh.close()


if __name__ == '__main__':
    sys.exit(main())