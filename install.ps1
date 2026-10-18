# One-shot installer for the "pop" OpenCode skill (concert_photo_gallery).
#
#   irm https://laotree.github.io/opencode-concert-gallery/install.ps1 | iex
#
# Checks the environment, installs OpenCode V2 if missing, and downloads the
# skill + gallery builder into <dir>\.opencode\skills\pop\.
# No git required. Idempotent: safe to re-run.
[CmdletBinding()]
param(
  [string]$Dir   = (Join-Path $HOME 'concert-photo-gallery'),
  [string]$SkillsDir = '.opencode\skills',
  [string]$Id    = 'pop',
  [string]$Base  = $(if ($env:SKILL_BASE) { $env:SKILL_BASE } else { 'https://laotree.github.io/opencode-concert-gallery' }),
  [string]$Local = '',
  [switch]$NoOpencode
)

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Repo = 'Laotree/opencode-concert-gallery'
$Dist = 'skill/pop'
$Dest = Join-Path (Join-Path $Dir $SkillsDir) $Id

function Say  ($m) { Write-Host $m }
function Ok   ($m) { Write-Host "  [ok] $m"   -ForegroundColor Green }
function Warn ($m) { Write-Host "  [!]  $m"   -ForegroundColor Yellow }
function Die  ($m) { Write-Host "  [x]  $m"   -ForegroundColor Red; exit 1 }
function Step ($m) { Write-Host ""; Write-Host "> $m" -ForegroundColor White }

Say ""
Say "Concert Photo Gallery - 一键安装"
Say "技能装到 $Dest"

# ---------------------------------------------------------------- 1. platform
Step '1/4  检查环境'
$arch = switch ($env:PROCESSOR_ARCHITECTURE) {
  'AMD64' { 'x64' }
  'ARM64' { 'arm64' }
  'x86'   { 'x86' }
  default { 'x64' }
}
Ok "Windows $([Environment]::OSVersion.Version) · $arch"
Ok "PowerShell $($PSVersionTable.PSVersion)"

$Py = $null
foreach ($c in @('python', 'py')) {
  $exe = Get-Command $c -ErrorAction SilentlyContinue
  if ($exe) { $Py = $c; break }
}
if ($Py) {
  $ver = (& $Py -c "import platform;print(platform.python_version())" 2>$null)
  Ok "python $ver"
} else {
  Warn '没找到 python —— 画廊生成器需要它（技能和 OpenCode 仍会装好）'
  Say  '     装一个：winget install Python.Python.3.12  或  https://www.python.org/downloads/'
}

# ---------------------------------------------------------------- 2. opencode
Step '2/4  检查 OpenCode V2'
if ($NoOpencode) {
  Warn '已按 -NoOpencode 跳过'
} else {
  $have = $null
  if (Get-Command opencode -ErrorAction SilentlyContinue) {
    $have = (& opencode --version 2>$null)
  }
  if ($have -match 'v?2\.') {
    Ok "已安装：$have"
  } else {
    if ($have) { Warn "检测到旧版本（$have），将安装 V2" }
    $url = "https://opencode.ai/update/api/latest/cli/opencode/opencode-windows-$arch.zip"
    $binDir = Join-Path $env:LOCALAPPDATA 'opencode\bin'
    $zip    = Join-Path $env:TEMP "opencode-$arch.zip"
    Say "  ->  $url"
    try {
      Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
      New-Item -ItemType Directory -Force -Path $binDir | Out-Null
      Expand-Archive -Path $zip -DestinationPath $binDir -Force
      Remove-Item $zip -Force
      $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
      if ($userPath -notlike "*$binDir*") {
        [Environment]::SetEnvironmentVariable('Path', "$userPath;$binDir", 'User')
      }
      $env:Path = "$env:Path;$binDir"
      Ok "安装到 $binDir（已加入用户 PATH）"
      Warn '新开一个终端让 PATH 生效'
    } catch {
      Die "OpenCode 下载失败：$_`n     手动安装见 https://opencode.ai/v2/docs/"
    }
  }
}

# ---------------------------------------------------------------- 3. skill
Step '3/4  下载技能文件'
New-Item -ItemType Directory -Force -Path (Join-Path $Dest 'scripts') | Out-Null
if ($Local) {
  if (-not (Test-Path (Join-Path $Local 'SKILL.md'))) { Die "-Local 指向的目录里没有 SKILL.md" }
  Copy-Item (Join-Path $Local 'SKILL.md') $Dest -Force
  Copy-Item (Join-Path $Local 'scripts\build_gallery.py') (Join-Path $Dest 'scripts') -Force
  Ok "从本地复制：$Local"
} else {
  try {
    Invoke-WebRequest -Uri "$Base/$Dist/SKILL.md" -OutFile (Join-Path $Dest 'SKILL.md') -UseBasicParsing
    Ok 'SKILL.md'
    Invoke-WebRequest -Uri "$Base/$Dist/scripts/build_gallery.py" -OutFile (Join-Path $Dest 'scripts\build_gallery.py') -UseBasicParsing
    Ok 'scripts\build_gallery.py'
  } catch {
    Die "下载失败：$_"
  }
}

# ---------------------------------------------------------------- 4. verify
Step '4/4  校验'
if (-not (Select-String -Path (Join-Path $Dest 'SKILL.md') -Pattern '^description:' -Quiet)) {
  Die 'SKILL.md 缺少 description，模型不会自动发现它'
}
Ok 'frontmatter 含 description'
if ($Py) {
  & $Py -m py_compile (Join-Path $Dest 'scripts\build_gallery.py')
  if ($LASTEXITCODE -eq 0) { Ok 'build_gallery.py 语法通过' } else { Die 'build_gallery.py 语法错误' }
  Remove-Item (Join-Path $Dest 'scripts\__pycache__') -Recurse -Force -ErrorAction SilentlyContinue
} else {
  Warn '跳过语法校验（没有 python）'
}
if ((Get-Item (Join-Path $Dest 'SKILL.md')).Length -eq 0) { Die '文件不完整' }
Ok "技能 ID：$Id"

Say ""
Write-Host "完成。" -ForegroundColor Green
Say "技能位置：$Dest"
Say ""
Say '接下来'
Say "  1)  cd `"$Dir`"; opencode"
Say '  2)  在 TUI 里按 /connect 登录一个模型'
Say "  3)  输入 @$Id 帮我找 <偶像> <场次> 的照片并做成画廊"
Say ""
Say '  使用边界：仅供个人查看，不得二次分发或商用。'
Say "  详见 https://github.com/$Repo/blob/main/DISCLAIMER.md"
Say ""
