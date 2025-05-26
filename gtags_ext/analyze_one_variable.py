import os
import re
import subprocess
import sys

def analyze_variable(var_name):
    result = subprocess.run(['global', '-gx', var_name], capture_output=True, text=True)
    lines = result.stdout.strip().split('\n')

    sources, destinations = set(), set()
    assign_pattern = re.compile(rf'\b{re.escape(var_name)}\b\s*(=|\+\+|--|\+=|-=|\*=|/=)')

    for line in lines:
        if not line.strip():
            continue

        # 1. まずタブで分割を試みる
        parts = line.split('\t')
        if len(parts) >= 4:
            _, _, file, code = parts[:4]
        else:
            # 2. タブで不十分ならスペース区切りで再挑戦（柔軟対応）
            match = re.match(rf'^{re.escape(var_name)}\s+(\d+)\s+([^\s]+)\s+(.*)$', line)
            if not match:
                print(f"⚠️  無効な行（スキップ）: {line}")
                continue
            _, file, code = match.groups()

        if assign_pattern.search(code):
            sources.add(file)
        else:
            destinations.add(file)

    return sources, destinations

def generate_plantuml(var_name, sources, destinations):
    lines = ['@startuml', 'skinparam linetype ortho']

    # ディレクトリ名だけに変換
    source_dirs = {os.path.dirname(path) for path in sources}
    dest_dirs = {os.path.dirname(path) for path in destinations}
    all_dirs = source_dirs | dest_dirs

    # 表示用コンポーネント名（/ や . を _ に変換）
    alias_map = {d: d.replace('/', '_').replace('.', '_') for d in all_dirs}

    # コンポーネント定義
    for d, alias in alias_map.items():
        lines.append(f'component "{d}" as {alias}')

    # 依存関係定義（ディレクトリ単位）
    for dst_dir in dest_dirs:
        dst_alias = alias_map[dst_dir]
        for src_dir in source_dirs:
            if src_dir != dst_dir:
                src_alias = alias_map[src_dir]
                lines.append(f'{src_alias} --> {dst_alias} : {var_name}')

    lines.append('@enduml')
    return '\n'.join(lines)

    # コンポーネント定義
    for comp in components:
        alias = comp.replace('/', '_').replace('.', '_')  # 別名（PlantUML用）
        lines.append(f'component "{comp}" as {alias}')

    # 矢印描画
    for dst in destinations:
        dst_alias = dst.replace('/', '_').replace('.', '_')
        for src in sources:
            src_alias = src.replace('/', '_').replace('.', '_')
            lines.append(f'{src_alias} --> {dst_alias} : {var_name}')

    lines.append('@enduml')
    return '\n'.join(lines)

def main():
    if len(sys.argv) < 2:
        print("❌ 使用法: python analyze_one_variable.py <変数名>")
        return

    var = sys.argv[1]
    print(f"📌 指定された変数名: {var}")

    sources, destinations = analyze_variable(var)

    if not sources and not destinations:
        print("⚠️  global による解析結果が空、または代入/参照なし。")

    puml_text = generate_plantuml(var, sources, destinations)
    with open('module_diagram.puml', 'w') as f:
        f.write(puml_text)

    print("✅ 出力ファイル: module_diagram.puml")
    print("--- 出力内容 ---")
    print(puml_text)

if __name__ == '__main__':
    main()
