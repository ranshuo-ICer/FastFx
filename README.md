# FastFx

一个用于外接键盘功能键模拟的 Windows 工具，让你的普通键盘拥有额外功能键！

## 功能特点

- 默认 F1~F12 为自定义快捷功能（如音量调节、打开软件）
- 按住 ESC 键暂时恢复标准功能键（Fn 模式）
- 支持任务栏托盘切换状态和配置界面
- 支持开机自启动
- 可自定义每个功能键的行为

## 使用方式

1. 下载并运行 `dist/FastFx.exe`
2. 托盘图标显示当前模式（M 表示自定义模式，Fn 表示标准模式）
3. 右键点击托盘图标可打开配置界面、切换模式或退出程序
4. 在配置界面中设置每个功能键的行为
5. 开启"开机自启动"选项以在系统启动时自动运行

## 自定义配置

程序会在运行目录下生成 `keymap.json` 文件，你可以直接编辑该文件或通过配置界面修改功能键映射。

示例配置：
```json
{
    "f1": "volume mute",
    "f2": "volume down",
    "f3": "volume up",
    "f4": "play/pause",
    "f5": "next track",
    "f6": "previous track",
    "f7": "",
    "f8": "",
    "f9": "",
    "f10": "",
    "f11": "brightness down",
    "f12": "brightness up"
}
```

## 构建说明

如果你想自行构建项目：

1. 克隆仓库
2. 安装依赖：`pip install -r requirements.txt`
3. 运行打包命令：`pyinstaller main.spec`
4. 可执行文件将生成在 `dist` 目录下

## 许可证

本项目采用 MIT 许可证 - 详情请见 [LICENSE](LICENSE) 文件

## 作者

SHuo RAN