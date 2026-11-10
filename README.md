# Consolas Mono

将 Consolas 的常用拉丁字母、数字和标点移植到 JetBrains Mono Nerd Font Mono 的
等宽网格中。支持 Regular、Bold、Italic 和 Bold Italic 四个样式。

本仓库发布构建、预览和安装脚本。字体和预览图是使用者在本地生成的产物。

## 本地构建

构建需要 Python、fontTools，以及具备相应修改授权的字体输入。预览另外需要 Pillow。
默认从 `C:/Windows/Fonts` 读取下列文件，字体放在其他目录时可传入 `--fonts-dir`。

- `JetBrainsMonoNerdFontMono-{Regular,Bold,Italic,BoldItalic}.ttf`
- `consola.ttf`、`consolab.ttf`、`consolai.ttf`、`consolaz.ttf`

```bash
python -m pip install fonttools pillow
python build_consolas_mono.py
python preview.py
```

构建输出到 `dist/ConsolasMono-*.ttf`。预览脚本使用默认字体目录，生成
`dist/preview.png`、`dist/preview-small.png` 和 `dist/preview-styles.png`。

## 设计

- 覆盖范围：Basic Latin、Latin-1 Supplement、Latin Extended-A，以及常用英文
  标点和符号。以 JetBrains Mono Nerd Font Mono 3.3.0 和 Consolas 7.01
  构建时，每个样式替换 334 个码位。
- 缩放：Consolas 的 1126/2048 em 单元格等比映射到 JetBrains Mono 的
  600/1000 em 单元格。字宽、基线和行高沿用 JetBrains Mono。
- Nerd Font 图标、Powerline 和框线沿用底版。引用被替换字形的复合字形会在替换前
  展开，保留原轮廓。展开的复合字形和移植的 Consolas 字形失去原有的 hinting，
  小字号下的笔画像素可能有差异。
- 保留底版的 `calt` 连字、风格集及其显示名称。编程连字和变体字形沿用底版。

## 安装

当前用户安装（无需管理员权限）：

```powershell
pwsh -NoProfile -File .\install_user_fonts.ps1
```

或直接双击 `dist` 下的四个 `.ttf` 选择“安装”。安装后重启终端，在字体设置中
选择 **Consolas Mono**。按当前用户安装的文件位于
`%LOCALAPPDATA%\Microsoft\Windows\Fonts`，注册表项位于
`HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts`。

## 授权

本仓库的脚本按 [MIT 许可证](LICENSE) 发布。字体输入及其中的轮廓适用各自的许可。

- JetBrains Mono 使用 [SIL Open Font License 1.1](https://www.jetbrains.com/lp/mono/#license)。
  图标来源和许可见 [Nerd Fonts 的 JetBrains Mono 说明](https://github.com/ryanoasis/nerd-fonts/tree/master/patched-fonts/JetBrainsMono)。
- Consolas 版权归 Microsoft Corporation 所有。Windows 随附字体的许可不授予修改或再分发权。
  使用 Consolas 作为构建输入前须取得相应许可。 [Microsoft 字体许可说明](https://learn.microsoft.com/en-us/typography/fonts/font-faq#redistribution-and-extended-rights)
