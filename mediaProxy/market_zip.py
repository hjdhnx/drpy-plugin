# MediaProxy DsPlayer 市场包打包脚本（python 3，Windows 构建机）。
#
# 市场形态：plugin.json（根部）+ bin/（当前全平台二进制；本体
# installFromEntries 只落当前平台项，zip 携双平台属设计内）。
# android 二进制自 1.1.1 起未变动——重编会因 ldflags 构建时间产生
# 无意义 diff，升级时用 --android 传入既有包原样搬运。
#
# 用法：
#   go 构建 win：CGO_ENABLED=0 GOOS=windows GOARCH=amd64 go build \
#     -ldflags="-s -w -X main.Version=$(git describe --tags --always)" \
#     -trimpath -o build/mediaProxy_windows_amd64.exe .
#   打包：python market_zip.py --ver 1.2.0 \
#     --android <mediaProxy-android ELF> --win build/mediaProxy_windows_amd64.exe
import argparse
import hashlib
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))

PLUGIN_JSON = '''{
  "name": "mediaProxy",
  "version": "{ver}",
  "title": "Go 媒体代理服务",
  "desc": "Go 媒体代理服务（leader-follower 流式分段引擎，秒级起播，支持 Range/拖动）",
  "author": "hjdhnx",
  "runtime": "binary",
  "params": "-port 5575",
  "env": {},
  "binaries": {
    "win32": "mediaProxy-win.exe",
    "linux": "mediaProxy-linux",
    "android": "mediaProxy-android"
  },
  "homepage": "https://github.com/hjdhnx/drpy-node",
  "_source": "drpy-plugin-dist",
  "installMode": "import",
  "portField": "-port",
  "healthCheck": {
    "type": "http",
    "path": "/",
    "port": 5575,
    "timeoutMs": 3000
  }
}
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ver', required=True)
    ap.add_argument('--android', required=True, help='mediaProxy-android ELF 路径')
    ap.add_argument('--win', required=True, help='mediaProxy_windows_amd64.exe 路径')
    args = ap.parse_args()

    for f in (args.android, args.win):
        if not os.path.isfile(f):
            sys.exit(f'缺二进制: {f}')
    import json
    meta = PLUGIN_JSON.replace('{ver}', args.ver)
    json.loads(meta)  # 模板合法性自检

    out_dir = os.path.join(HERE, 'dist')
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f'mediaProxy-{args.ver}.zip')
    if os.path.isfile(out):
        os.remove(out)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zi = zipfile.ZipInfo('plugin.json')
        zi.external_attr = 0o644 << 16
        zi.compress_type = zipfile.ZIP_DEFLATED
        zf.writestr(zi, meta.encode('utf-8'))
        for rel, src in (('bin/mediaProxy-android', args.android),
                         ('bin/mediaProxy-win.exe', args.win)):
            zi = zipfile.ZipInfo(rel)
            zi.external_attr = 0o755 << 16
            zi.compress_type = zipfile.ZIP_DEFLATED
            with open(src, 'rb') as f:
                zf.writestr(zi, f.read())

    md5 = hashlib.md5(open(out, 'rb').read()).hexdigest()
    print(f'产物: {out}（{os.path.getsize(out)} bytes）')
    print(f'md5: {md5}')


if __name__ == '__main__':
    main()
