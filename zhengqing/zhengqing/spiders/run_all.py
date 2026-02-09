import os
import sys
import subprocess

# 获取当前脚本所在目录（确保路径正确）
current_dir = os.path.dirname(os.path.abspath(__file__))

# 严格指定执行顺序：先runner.py，后runner3.py
script_order = [
    "runner.py",
    "runner3.py"
]

# 可选配置：如果前一个脚本失败，是否终止后续脚本运行（建议开启）
STOP_ON_FAILURE = True


def run_single_script(script_name):
    """执行单个脚本，返回执行结果（成功/失败）"""
    script_path = os.path.join(current_dir, script_name)

    # 1. 检查脚本文件是否存在
    if not os.path.exists(script_path):
        print(f"❌ 致命错误：找不到脚本文件 {script_name}（路径：{script_path}）")
        return False

    # 2. 执行脚本
    print(f"\n=== 开始执行 {script_name} ===")
    result = subprocess.run(
        [sys.executable, script_path],  # 使用当前Python环境，避免路径问题
        capture_output=True,
        text=True
    )

    # 3. 打印执行结果
    if result.stdout:
        print(f"📌 {script_name} 输出内容：\n{result.stdout}")
    if result.stderr:
        print(f"⚠️  {script_name} 错误输出：\n{result.stderr}")

    # 4. 判断执行是否成功
    if result.returncode == 0:
        print(f"✅ {script_name} 执行成功！")
        return True
    else:
        print(f"❌ {script_name} 执行失败（退出码：{result.returncode}）")
        return False


if __name__ == "__main__":
    print("=== 开始按顺序执行脚本 ===")
    print(f"执行顺序：{script_order[0]} → {script_order[1]}")

    # 按顺序逐个执行脚本
    execution_success = True
    for script in script_order:
        # 执行当前脚本
        script_result = run_single_script(script)

        # 如果开启「失败终止」且当前脚本失败，直接退出
        if STOP_ON_FAILURE and not script_result:
            print(f"\n❌ {script} 执行失败，终止后续脚本运行！")
            execution_success = False
            break

    # 最终结果汇总
    print("\n=== 执行完成 ===")
    if execution_success:
        print("🎉 所有脚本均按顺序执行成功！")
        sys.exit(0)
    else:
        print("⚠️  脚本执行失败，请检查错误信息！")
        sys.exit(1)