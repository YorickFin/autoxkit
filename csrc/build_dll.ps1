# build_dll.ps1 - 一键编译 autoxhook.dll（MSYS2 ucrt64 工具链）
# 产物：autoxkit/hook/_autoxhook.dll（纯 Win32 C，跨 Python 3.10~3.13+）
# 用法：powershell -ExecutionPolicy Bypass -File csrc\build_dll.ps1
#
# 注意：本脚本必须用相对路径调用 gcc —— mingw ld 以 ANSI API 打开输出文件，
# 绝对路径中的中文目录（如"备份"）会被错误解码；进程当前目录则编码正确。

$ErrorActionPreference = "Stop"

# 工具链路径（按 MSYS2 实际安装环境自动探测）
$gccCandidates = @(
    "D:\Programs\msys64\ucrt64\bin\gcc.exe",
    "D:\Programs\msys64\mingw64\bin\gcc.exe"
)
$gcc = $null
foreach ($c in $gccCandidates) {
    if (Test-Path $c) { $gcc = $c; break }
}
if (-not $gcc) { throw "未找到 gcc，请检查 MSYS2 安装路径: $gccCandidates" }

Push-Location $PSScriptRoot
try {
    # -static-libgcc: 产物不依赖 libgcc DLL，拷到任何机器可加载
    # -s: 剥离符号     -O2: 优化     -Wall: 全警告
    # 不链接任何 Python 库 —— 这是跨 Python 版本的关键
    & $gcc -O2 -Wall -shared -s -static-libgcc -o _autoxhook.dll autoxhook.c -luser32 -lkernel32
    if ($LASTEXITCODE -ne 0) { throw "编译失败（gcc exit=$LASTEXITCODE）" }

    # PowerShell 的文件操作走 .NET 宽字符 API，中文路径安全
    $dest = Join-Path $PSScriptRoot "..\autoxkit\hook\_autoxhook.dll"
    Move-Item -Force (Join-Path $PSScriptRoot "_autoxhook.dll") $dest
    Write-Host "OK -> $((Resolve-Path $dest).Path)"
}
finally {
    Pop-Location
}
