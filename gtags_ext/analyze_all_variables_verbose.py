import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

OUTPUT_DIR = "puml"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_variables(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    pattern = re.compile(
        r'^\s*(boolean_T|uint8_T|uint16_T)\s+(\w+)\s*(?:=[^;]*)?;',
        re.MULTILINE
    )
    matches = pattern.findall(content)
    print(f"🔍 抽出された変数数: {len(matches)}")
    for var_type, var_name in matches:
        print(f"  - {var_type} {var_name}")
    return [name for _, name in matches]

def analyze_variable(var_name):
    print(f"🧪 global 検索中: {var_name}")
    result = subprocess.run(['global', '-gx', var_name], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"⚠️  global 実行エラー: {result.stderr}")
        return ""
    if not result.stdout.strip():
        print(f"⚠️  global による参照結果なし: {var_name}")
        return ""
    print(f"📝 global 出力 ({var_name}):\n{result.stdout}")
    return result.stdout.strip()

def generate_plantuml(var_declared_file, var_name, global_output):
    assign_pattern = re.compile(rf'\b{re.escape(var_name)}\b\s*(=|\+\+|--|\+=|-=|\*=|/=)')
    sources, destinations = set(), set()

    for line in global_output.splitlines():
        if not line.strip():
            continue
        m = re.match(r'^(\w+)\s+(\d+)\s+([^\s]+)\s+(.*)$', line)
        if not m:
            print(f"⚠️  パース失敗行（無視）: {line}")
            continue
        _, _, file, code = m.groups()

        if assign_pattern.search(code):
            sources.add(file)
        else:
            destinations.add(file)

    if not sources and not destinations:
        print(f"⚠️  {var_name}: 使用箇所なし（PlantUMLは生成されません）")
        return

    dirs = {os.path.dirname(p) for p in sources | destinations}
    alias = lambda d: d.replace('/', '_').replace('.', '_')

    lines = ['@startuml', 'title',  f'**{var_name}** (in {var_declared_file})', ' relation diagram ', 'end title', 'skinparam linetype ortho']
    for d in dirs:
        lines.append(f'component "{d}" as {alias(d)}')

    # 🔽 重複しないリンクを追加
    links = set()
    for dst in destinations:
        dst_alias = alias(os.path.dirname(dst))
        for src in sources:
            src_alias = alias(os.path.dirname(src))
            if src_alias != dst_alias:
                links.add((src_alias, dst_alias))

    for src_alias, dst_alias in sorted(links):
        lines.append(f'{src_alias} --> {dst_alias}')

    lines.append('@enduml')

    out_puml = os.path.join(OUTPUT_DIR, f"{var_name}.puml")
    with open(out_puml, "w") as f:
        f.write('\n'.join(lines))

    print(f"✅ {var_name}: PlantUMLファイルを出力しました: {out_puml}")

    try:
        subprocess.run(['docker', 'run', '--rm', '-v', f'{os.getcwd()}:/data',
                        'exmotion-rd/plantuml_jpfonts:latest', f'{OUTPUT_DIR}/{var_name}.puml'],
                       check=True)
        print(f"🖼️  {var_name}: PNG生成完了")
    except subprocess.CalledProcessError as e:
        print(f"❌ PNG生成エラー: {var_name} → {e}")

def main():
    if len(sys.argv) != 2:
        print("❌ 使用法: python analyze_all_variables.py <ソースファイル>")
        return

    source_file = sys.argv[1]
    if not os.path.isfile(source_file):
        print(f"❌ ファイルが見つかりません: {source_file}")
        return

    variables = extract_variables(source_file)
    if not variables:
        print("⚠️  定義された変数が見つかりませんでした。")
        return

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for var in variables:
            futures.append(executor.submit(lambda v: generate_plantuml(source_file, v, analyze_variable(v)), var))
        for f in futures:
            f.result()

if __name__ == "__main__":
    main()
