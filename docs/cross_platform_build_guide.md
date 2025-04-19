# VocabMaster 跨平台打包指南

本文档提供了在不同操作系统上构建 VocabMaster 应用程序的详细说明。

## 环境要求

在所有平台上，您需要：

- Python 3.8 或更高版本
- pip 包管理器
- 项目依赖项（见 `requirements.txt`）

## 安装依赖

在任何平台上，首先克隆或下载项目，然后安装依赖：

```bash
pip install -r requirements.txt
```

## Windows 平台打包

1. 确保已安装所有依赖
2. 运行打包脚本：

```bash
python build_app.py
```

3. 打包完成后，可执行文件将位于 `dist` 目录中，名为 `VocabMaster.exe`

## macOS 平台打包

1. 确保已安装所有依赖（包括 macOS 特定依赖）
2. 运行打包脚本：

```bash
python build_app.py
```

3. 打包完成后，可执行文件将位于 `dist` 目录中，名为 `VocabMaster`
4. 为可执行文件添加执行权限：

```bash
chmod +x dist/VocabMaster
```

### macOS 注意事项

- 如果您使用的是 Apple Silicon (M1/M2) 芯片，打包脚本会自动创建通用二进制文件
- 首次运行时，macOS 可能会显示安全警告，您需要在系统偏好设置中允许运行

## Linux 平台打包

1. 确保已安装所有依赖
2. 运行打包脚本：

```bash
python build_app.py
```

3. 打包完成后，可执行文件将位于 `dist` 目录中，名为 `VocabMaster`
4. 为可执行文件添加执行权限：

```bash
chmod +x dist/VocabMaster
```

### Linux 注意事项

- 在不同的 Linux 发行版上，可能需要安装额外的系统依赖，特别是与 Qt 相关的库
- 在 Ubuntu/Debian 系统上，可能需要：
  ```bash
  sudo apt-get install libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-xkb1 libxkbcommon-x11-0
  ```

## 常见问题解决

### 找不到模块

如果打包过程中报错找不到某个模块，请确保该模块已在 `requirements.txt` 中列出并已安装。

### 图标问题

- Windows 平台需要 `.ico` 格式图标
- macOS 平台需要 `.icns` 格式图标
- Linux 平台可以使用 `.png` 格式图标

如果缺少特定平台的图标，打包脚本会尝试使用通用的 PNG 图标作为备选。

### 运行时错误

如果打包后的应用程序无法运行，请检查日志文件（位于应用程序同目录下的 `logs` 文件夹）以获取详细错误信息。

## Docker 容器化（可选）

对于需要在容器环境中运行的用户，可以考虑使用 Docker：

1. 创建 Dockerfile（项目根目录下）
2. 构建镜像：

```bash
docker build -t vocabmaster .
```

3. 运行容器：

```bash
docker run -p 8080:8080 vocabmaster
```

注意：Docker 容器化需要额外的配置来支持 GUI 应用程序，这超出了本指南的范围。