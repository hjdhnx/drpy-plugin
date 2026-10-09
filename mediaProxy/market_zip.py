# MediaProxy DsPlayer 市场包打包脚本（python 3，Windows 构建机）。
#
# 2026-10-10 起单平台出包（MARKET-PLATFORM-ADAPT-DESIGN §6.2 拆包，R2 禁
# 多合一）：安卓包 id=mediaProxy（bin/ 只含 ELF），win 包 id=mediaProxy-win
# （bin/ 只含 PE，独立版本线 1.0.0 起）——一个条目一个平台，包内不含对方
# 平台死重。市场条目 id 必须逐字等于包内 plugin.json 的 name。
# android 二进制自 1.1.1 起未变动——重编会因 ldflags 构建时间产生
# 无意义 diff，升级时用 --android 传入既有包原样搬运。
#
# 用法：
#   go 构建 win：CGO_ENABLED=0 GOOS=windows GOARCH=amd64 go build \
#     -ldflags="-s -w -X main.Version=$(git describe --tags --always)" \
#     -trimpath -o build/mediaProxy_windows_amd64.exe .
#   安卓包：python market_zip.py --ver 1.2.2 --platform android \
#     --android build/mediaProxy-android
#   win 包：python market_zip.py --ver 1.0.0 --platform win32 \
#     --win build/mediaProxy-win.exe
import argparse
import hashlib
import json
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))

# name 按平台定死（R4 命名约定），binaries 只声明当前平台键。
# 包内布局与 1.2.1 同构：二进制落 bin/ 目录，binaries 值为纯文件名
#（不带 bin/ 前缀）——本体 _findEntry 先查 bin/<file> 再查包根，
# 纯文件名声明对老/新本体都落在 bin/<file>（带前缀会在老本体拼出
# bin/bin/ 死路径，剥前缀归一仅 2026-10-09 后新本体有）。
PLATFORM_SPEC = {
    'android': {
        'name': 'mediaProxy',
        'bin_arg': '--android',
        'binary': 'mediaProxy-android',
        'platform_key': 'android',
    },
    'win32': {
        'name': 'mediaProxy-win',
        'bin_arg': '--win',
        'binary': 'mediaProxy-win.exe',
        'platform_key': 'win32',
    },
}


def plugin_json(ver: str, name: str, platform_key: str, binary: str) -> str:
    return json.dumps({
        'name': name,
        'version': ver,
        'title': 'Go 媒体代理服务',
        'desc': 'Go 媒体代理服务（leader-follower 流式分段引擎，秒级起播，支持 Range/拖动）',
        'author': 'hjdhnx',
        'runtime': 'binary',
        'params': '-port 5575',
        'env': {},
        'binaries': {platform_key: binary},
        'homepage': 'https://github.com/hjdhnx/drpy-node',
        '_source': 'drpy-plugin-dist',
        'installMode': 'import',
        'portField': '-port',
        'healthCheck': {
            'type': 'http',
            'path': '/',
            'port': 5575,
            'timeoutMs': 3000,
        },
    }, ensure_ascii=False, indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ver', required=True)
    ap.add_argument('--platform', required=True, choices=sorted(PLATFORM_SPEC))
    ap.add_argument('--android', help='mediaProxy-android ELF 路径')
    ap.add_argument('--win', help='mediaProxy_windows_amd64.exe 路径')
    args = ap.parse_args()

    spec = PLATFORM_SPEC[args.platform]
    src = getattr(args, spec['bin_arg'].lstrip('-'))
    if not src:
        sys.exit(f"platform={args.platform} 需要 {spec['bin_arg']} 指定二进制")
    if not os.path.isfile(src):
        sys.exit(f'缺二进制: {src}')

    name = spec['name']
    out_dir = os.path.join(HERE, 'dist')
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f'{name}-{args.ver}.zip')
    if os.path.isfile(out):
        os.remove(out)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zi = zipfile.ZipInfo('plugin.json')
        zi.external_attr = 0o644 << 16
        zi.compress_type = zipfile.ZIP_DEFLATED
        zf.writestr(zi, plugin_json(
            args.ver, name, spec['platform_key'], spec['binary']).encode('utf-8'))
        zi = zipfile.ZipInfo(f"bin/{spec['binary']}")
        zi.external_attr = 0o755 << 16
        zi.compress_type = zipfile.ZIP_DEFLATED
        with open(src, 'rb') as f:
            zf.writestr(zi, f.read())

    md5 = hashlib.md5(open(out, 'rb').read()).hexdigest()
    print(f'产物: {out}（{os.path.getsize(out)} bytes）')
    print(f'md5: {md5}')


if __name__ == '__main__':
    main()
