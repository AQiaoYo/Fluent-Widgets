# 标准库导入
import os
import subprocess


def format_python_files(directory):
    # 获取目录下所有的 Python 文件
    py_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))

    # # 使用 black 格式化所有 Python 文件
    # for file in py_files:
    #     print(f"Formatting with black: {file}")
    #     subprocess.run(["python", "-m", "black", file])

    # 使用 isort 对所有 Python 文件优化导入
    for file in py_files:
        print(f"使用 isort 优化导入: {file}")
        subprocess.run(["python", "-m", "isort", file])

    # 使用 autoflake 删除未使用的导入
    for file in py_files:
        print(f"使用 autoflake 删除未使用的导入: {file}")
        subprocess.run(["python", "-m", "autoflake", "--remove-unused-variables", "--in-place", file])


if __name__ == "__main__":
    # 设置需要格式化的文件夹路径
    folder_path = "./qfluentwidgets"  # 替换为你的文件夹路径
    format_python_files(folder_path)
