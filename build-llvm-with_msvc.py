import os
import subprocess
import sys
import json
from pathlib import Path
from shutil import which

# 1. 配置路径
PROJECT_ROOT = Path(__file__).parent.resolve()
LLVM_CMAKE_DIR = PROJECT_ROOT / "llvm"
BUILD_DIR = LLVM_CMAKE_DIR / "build"

def find_vs_tools():
    """使用 vswhere 工具自动查找 Visual Studio 安装路径及其内置的 cmake, ninja"""
    print("正在寻找 Visual Studio 安装路径及内置工具链...")

    program_files = os.environ.get("ProgramFiles(x86)", os.environ.get("ProgramFiles", "C:\\Program Files (x86)"))
    vswhere_path = Path(program_files) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"

    if not vswhere_path.exists():
        print(f"错误: 找不到 vswhere.exe，路径尝试: {vswhere_path}")
        sys.exit(1)

    try:
        output = subprocess.check_output([
            str(vswhere_path),
            "-latest",
            "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
            "-format", "json",
            "-utf8"
        ])
        vs_info = json.loads(output)
        if not vs_info:
            raise RuntimeError("未找到包含 C++ 编译工具的 Visual Studio 版本。")

        vs_path = Path(vs_info[0]["installationPath"])
        print(f"找到 Visual Studio: {vs_path}")

        cmake = None
        ninja = None

        # 寻找 VS 自带的 cmake.exe 和 ninja.exe
        cmake_extension_dir = vs_path / "Common7" / "IDE" / "CommonExtensions" / "Microsoft" / "CMake"
        if cmake_extension_dir.exists():
            cmake_matches = list(cmake_extension_dir.glob("**/bin/cmake.exe"))
            if cmake_matches:
                cmake = cmake_matches[0]

            ninja_matches = list(cmake_extension_dir.glob("**/ninja.exe"))
            if ninja_matches:
                ninja = ninja_matches[0]

        # 降级备用方案：从系统环境变量中查找
        if not cmake:
            system_cmake = which("cmake")
            if system_cmake:
                cmake = Path(system_cmake)
                print("未找到 VS 自带 CMake，已回退到系统 CMake")
        if not ninja:
            system_ninja = which("ninja")
            if system_ninja:
                ninja = Path(system_ninja)
                print("未找到 VS 自带 Ninja，已回退到系统 Ninja")

        if not cmake or not ninja:
            raise RuntimeError("未能找齐 CMake 或 Ninja 编译工具，请检查环境。")

        return vs_path, cmake.resolve(), ninja.resolve()

    except Exception as e:
        print(f"自动查找编译工具失败: {e}")
        sys.exit(1)


def get_vs_env(vs_path: Path) -> dict:
    """通过 vcvarsall.bat 动态获取 x64 架构的 MSVC 编译环境变量"""
    vcvarsall_path = vs_path / "VC" / "Auxiliary" / "Build" / "vcvarsall.bat"
    if not vcvarsall_path.exists():
        print(f"错误: 找不到 vcvarsall.bat, 路径: {vcvarsall_path}")
        sys.exit(1)

    print("正在初始化 MSVC x64 编译环境...")
    # 执行 vcvarsall.bat amd64 获取 x64 编译环境
    cmd = f'"{vcvarsall_path}" amd64 && set'

    current_env = os.environ.copy()
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=current_env)
    if res.returncode != 0:
        print("错误: 初始化 MSVC 环境失败")
        sys.exit(1)

    vs_env = {}
    for line in res.stdout.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            vs_env[key] = value

    return vs_env


def build_llvm(vs_path, cmake_path, ninja_path):
    """配置并编译 LLVM/Clang 项目"""
    print(f"\n" + "=" * 50)
    print(" 开始编译 LLVM (x64 Release) ".center(50, "="))
    print(f"=" * 50)

    # 1. 获取 MSVC x64 环境变量
    env = get_vs_env(vs_path)

    # 2. CMake 配置阶段
    cmake_configure_cmd = [
        str(cmake_path),
        "-S", str(LLVM_CMAKE_DIR),
        "-B", str(BUILD_DIR),
        "-G", "Ninja",
        f"-DCMAKE_MAKE_PROGRAM={ninja_path}",
        "-DCMAKE_BUILD_TYPE=Release",
        "-DLLVM_ENABLE_PROJECTS=clang",         # 核心：必须启用 Clang 项目以生成 clang-cl
        "-DLLVM_TARGETS_TO_BUILD=X86",          # 优化：仅编译 X86/X64 后端，大幅加快编译速度
        "-DLLVM_INCLUDE_TESTS=OFF",             # 优化：关闭测试用例
        "-DLLVM_INCLUDE_BENCHMARKS=OFF",        # 优化：关闭基准测试
        
        # 显式强制 MSVC 编译器使用 UTF-8 编码解析源码和输出
        "-DCMAKE_C_FLAGS=/utf-8",
        "-DCMAKE_CXX_FLAGS=/utf-8",
    ]

    print(f"运行 CMake 配置...")
    res = subprocess.run(cmake_configure_cmd, env=env)
    if res.returncode != 0:
        print("错误: CMake 配置失败")
        sys.exit(1)

    # 3. CMake 构建阶段
    print(f"运行 CMake 构建 (目标: clang)...")
    cmake_build_cmd = [
        str(cmake_path),
        "--build", str(BUILD_DIR),
        "--config", "Release",
        "--target", "clang",                    # 只精准编译 clang 本身，不浪费时间给周边工具
        "--parallel"
    ]

    res = subprocess.run(cmake_build_cmd, env=env)
    if res.returncode != 0:
        print("错误: CMake 构建失败")
        sys.exit(1)

    print(f"\nLLVM/Clang 编译顺利完成！")
    print(f"编译产物目录: {BUILD_DIR}")


def main():
    if not LLVM_CMAKE_DIR.exists():
        print(f"错误: 找不到 LLVM CMakeLists 目录，预期路径为: {LLVM_CMAKE_DIR.resolve()}")
        sys.exit(1)

    # 1. 自动化寻找工具链
    vs_path, cmake_path, ninja_path = find_vs_tools()
    print(f"VS 根目录:      {vs_path}")
    print(f"使用 CMake:     {cmake_path}")
    print(f"使用 Ninja:     {ninja_path}")

    # 2. 执行编译
    build_llvm(vs_path, cmake_path, ninja_path)


if __name__ == "__main__":
    main()