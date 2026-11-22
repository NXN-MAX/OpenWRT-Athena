[简体中文](README.md) · [English](README.en.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [العربية](README.ar.md)

# Athena v0.0.6

Athena 是采用 HeroUI 设计语言的原生 OpenWrt LuCI 主题，提供玻璃质感界面、动态状态卡片，以及统一的表格、表单和弹窗。支持浅色、深色和跟随系统模式，适配电脑、平板与手机。

服务端模板和素材管理 RPC 均使用 **ucode**；浏览器端使用 LuCI 自带的 JavaScript、`form`、`ui`、`rpc`、`poll` 和 UCI 接口。主题不依赖 Lua 兼容层，也不包含 React、ReactDOM 或 Argon 的 CSS/脚本。默认登录页直接以原生 HTTP 表单提交，不在未认证状态启动 LuCI RPC；带脚本的认证插件保留原生初始化接口。

浏览器标题只显示 OpenWrt 原生系统主机名，不附加固定主题名或页面名。主机名通过 LuCI 的“系统 → 系统 → 通用设置 → 主机名”管理；主题外观设置不重复提供系统配置项。侧边导航顶部以两行显示 OpenWRT / Athena，右侧显示系统版本；底部 GitHub 链接显示当前主题版本。

## 界面预览

以下截图来自本地 OpenWrt 25.12.6 开发环境的深色模式；页面语言、版本号和软件包列表以实际环境为准。

### 网络概览

互联网连接、系统负载、内存与液态存储卡片集中展示，设备详情可折叠查看。

![网络概览](https://raw.githubusercontent.com/NXN-MAX/OpenWRT-Athena/main/doc/screenshots/overview-dark.jpg)

### Athena 主题设置

统一管理默认外观、登录布局、自定义图标与背景，并从正式 Release 检查更新。

![Athena 主题设置](https://raw.githubusercontent.com/NXN-MAX/OpenWRT-Athena/main/doc/screenshots/theme-settings.jpg)

### 软件管理

为 LuCI 原生软件管理提供统一的筛选、安装入口、标签页和软件包表格，保留原生包管理流程。

![软件管理](https://raw.githubusercontent.com/NXN-MAX/OpenWRT-Athena/main/doc/screenshots/package-manager.jpg)

## GitHub 版本检查与在线更新

系统菜单中的「Athena主题」提供版本检查和在线更新。更新源固定为 [NXN-MAX/OpenWRT-Athena 的正式 Releases](https://github.com/NXN-MAX/OpenWRT-Athena/releases)。未发布正式版本时显示「暂无正式发布版本」；只允许安装比当前版本新的稳定版。

发布包命名为 `luci-theme-athena-X.Y.Z.tar.gz`。更新检查只读取正式 Release 附件 `athena-release.json`（`releases/latest/download/athena-release.json`），不依赖 GitHub API、仓库分支或第三方镜像。清单由发布流程按实际归档生成，记录稳定版本、下载地址、字节数与 SHA256。更新接口核对仓库、版本标签、安装包名称、大小和清单中的 SHA256 digest，下载后再次校验；拒绝路径穿越、链接文件和缺失关键文件的归档。模板与更新脚本先编译/检查，再替换主题自身文件，静态资源版本最后切换。状态文件放在 root 私有的 `/var/run/athena-update/`，安装过程不占用长时间 RPC 请求。

更新前，旧主题和 Athena 配置保存在 `/etc/athena/backups/`；复制失败会自动回滚。现有 Athena 配置与上传素材保留。更新成功后重新加载页面。备份可通过 `tar -xzf <备份文件> -C /` 恢复，再重载 rpcd。本更新方式安装原生预构建归档；通过 SDK 软件包安装时，包管理器的版本记录由对应软件包管理。

更新功能依赖 `curl` 和 `ca-bundle`，SDK 的 Makefile 已声明依赖。手动安装时请先确保它们可用。GitHub 请求、下载或校验失败会显示失败状态，保留当前主题。

## 构建与发布

```sh
npm ci
npm run build
npm test
npm run pack
```

`dist/` 包含可直接安装的原生预构建归档和 SHA256 文件，不含 node_modules、工作区密钥或用户上传素材。Makefile 与 package.json 的语义版本必须一致；构建会生成 `release-version`，供侧栏和更新接口共同读取。资源哈希 `version` 只用于浏览器缓存。

构建会校正安装器、设备检查脚本和更新器的可执行权限；安装器也会设置路由器端更新器权限，兼容网页上传或 ZIP 导出丢失文件模式的情况。

GitHub Actions 在 main 推送和 Pull Request 上执行构建、样式规范检查与回归检查。main 的版本文件变更会自动构建并发布对应版本（当前为 `v0.0.6`），生成标签、安装包和 SHA256，供在线更新使用；也支持推送一致的稳定版标签，或在 Actions → Stable release → Run workflow 手动发布。已发布版本会跳过，后续发布应先增加 package.json 和 Makefile 版本。

OpenWrt 设备上的接口与更新器隔离检查：

```sh
ATHENA_SSH=/path/to/device-ssh scripts/test-device.sh
ATHENA_SSH=/path/to/device-ssh python3 scripts/test-updater-device.py
```

`device-ssh` 为开发者自己的 SSH 包装命令，不应提交私钥。更新器测试仅写入设备 `/tmp/athena-updater-test/`，覆盖安装、备份、回滚、校验错误、路径穿越、链接文件及配置/素材保留。

实际使用官方 **`@heroui/styles` 3.2.7** 的 Button、ButtonGroup、Card、Typography、Input、Textarea、Select、Tabs、Table、Modal、Switch、ScrollShadow 等基础样式。该包支持不依赖框架的 HTML。LuCI 控件保留原节点和原事件，组件类直接加到原节点；表格、开关只增加必要的容器。勾选框保留原生控件及主题兼容样式。HeroUI React UIKit 不会发送到路由器。

自定义下拉项的“添加”按钮复用 LuCI 校验及 `createItems()`；布尔表格筛选保留原生的 0、1、未筛选状态。开关右侧的「全部」使用紧凑文字按钮，不保留胶囊底色和左右内边距；点击只清除当前列筛选，保留其他列条件；共享适配层统一处理所有原生布尔筛选，不为页面单独声明。弹出菜单及富文本悬浮详情优先使用浏览器 Popover 顶层，避开表格滚动容器的裁剪。右上角使用 LuCI 原生未保存配置计数，计数为 0 自动隐藏。

## 结构

- `ucode/template/themes/athena/*.ut`：ucode 页头、页尾、登录页。
- `htdocs/luci-static/resources/menu-athena.js`：原生导航、搜索、外观切换入口、概览摘要。
- `htdocs/luci-static/resources/athena/ui.js`：唯一公共控件适配层，保留原生表单、验证、事件和轮询。
- `htdocs/luci-static/resources/view/athena-config.js`：原生主题设置页。
- `root/usr/share/rpcd/ucode/luci.athena`：ucode 素材、版本检查与更新任务接口。
- `root/usr/libexec/athena-update`：隔离校验、备份和原子替换更新器。
- `root/usr/share/rpcd/acl.d/`、`root/usr/share/luci/menu.d/`：权限和菜单注册。
- `src/styles.css`：官方 HeroUI CSS 导入和原生布局、响应式适配。

## 配置

系统 → Athena主题：`/cgi-bin/luci/admin/system/athena`。

配置文件为 `/etc/config/athena`，保存主题色、默认外观模式和登录页布局。默认外观初始为「跟随系统」，也可选「暗黑模式」或「日光模式」。登录页与后台右上角复用同一个模式选择组件；手动选择会记在当前浏览器，尚未手动选择时使用主题设置的默认模式。设置页先显示主题更新，再显示外观与素材设置。自定义图标、浏览器图标和背景分开管理，正式版本检查和更新来自指定 GitHub 仓库。

登录页默认背景为项目提供的 `htdocs/luci-static/athena/login.svg`，线条随外观模式切换；旧的渐变、透镜和光线装饰已删除。默认图作为本地静态 SVG 加载，内容纳入资源缓存版本。登录面板与顶部导航共用毛玻璃规则，以参数调整透明度与模糊：导航使用 72%→44% 底色和 20px 模糊；登录面板使用 28%→14% 底色和 4px 模糊，让 SVG 纹理透出。分栏右侧面板上限为 390 CSS px，对应 2 倍屏截图中的 780 像素。两种登录模式在手机上统一使用全宽单栏，表单向上对齐并保留随视口高度调整的顶部间距。

登录页使用本地 SVG 背景，品牌统一放在认证表单上方。分栏版右侧玻璃面板从顶部贯穿到底部，无外部留白或圆角；电脑端另提供居中卡片布局。两种布局仅保留 Athena 品牌、认证表单及必要的错误提示，不显示标语或欢迎说明。输入框、按钮、密码显隐及文字类型复用已有公共组件，登录页只定义布局和背景。自定义图片或视频背景继续生效。手机上两种模式均为全宽单栏、表单向上对齐；浅色与深色随主题外观切换。

图标使用 PNG，16–1024 像素，最大 1 MiB；浏览器图标必须为正方形。背景支持 JPG、PNG、GIF、WebP、MP4、WebM，单个文件最大 20 MiB。上传经 LuCI 原生接口认证，ucode 验证文件类型、尺寸和路径后以 SHA256 文件名存储；设置清单原子写入。SVG/HTML 上传被拒绝。

## 签名软件源

推荐使用 [Athena 自有签名源](doc/signed-feed.md)安装和更新：支持 OpenWrt 24.10 的 opkg/IPK 与 25.12 的 APKv3，固定公钥验证，无需关闭签名检查。启用源后请通过 LuCI 软件管理更新，保持包管理器版本记录一致。此源为第三方源，官方收录尚在准备。

以下为独立 Release 文件的手动安装方式。

## OpenWrt 安装包

正式 Release 同时提供官方 SDK 构建的两种安装格式（架构 `all`）：

- OpenWrt 24.10、ucode LuCI、opkg：下载 `.ipk`，执行 `opkg install /tmp/luci-theme-athena_*.ipk`。
- OpenWrt 25.12、ucode LuCI、apk：下载 `.apk`，执行 `apk add --allow-untrusted /tmp/luci-theme-athena-*.apk`。独立 SDK 构建的包不使用 OpenWrt 官方软件源的签名，因此本地安装需要此参数。

先用 Release 的 `SHA256SUMS` 校验下载文件；依赖由设备自身对应版本的软件源解析。不要混用两个格式。现有配置与上传素材保留。卸载前先切换到其他已安装主题，再执行 `opkg remove luci-theme-athena` 或 `apk del luci-theme-athena`。

发布流程先构建并测试主题，再分别使用 OpenWrt 24.10 和 25.12 SDK 构建，两个包均成功后才创建 Release。以下归档安装方式继续供内置更新器及手动部署使用。

## 安装

路由器不需要 Node.js。构建输出已经放在 `htdocs`，可以使用包含静态资源的源码包：

```sh
# 路由器上，解压后的目录内执行：
sh scripts/install.sh
```

安装前需有 ucode 版 LuCI、`rpcd-mod-ucode`、`ucode-mod-fs` 和 `ucode-mod-uci`。安装脚本先编译检查模板和 RPC，再复制文件、注册主题。已有 `/etc/config/athena` 会保留。现有主题素材目录也会保留。

通过 OpenWrt SDK 编译时，将目录放到 SDK 的 package 目录，先在电脑上构建静态资源，再编译 `luci-theme-athena`。Makefile 也支持 LuCI 仓库的 `themes/` 目录。

在系统 → 系统 → 语言和界面中选择其他已安装主题可切换外观。切换不会删除 Athena 设置与素材；卸载主题包前请先切换到其他主题。

## 兼容性边界

实际运行环境是 OpenWrt **25.12.6 / armsr/armv8**，采用 ucode 模板与 rpcd ucode 插件，保留原生应用 API 和 UCI 保存流程。23.05 的 ucode 开发方式是实现目标；本轮没有 23.05 设备或镜像的运行验证，因此不宣称完成 23.05 实测。浏览器需支持现代 CSS（包括 `:has()`、`color-mix()`）与现代 JavaScript。

应用私有的原生逻辑仍由应用本身处理。第三方应用自身若依赖 Lua，其依赖与 Athena 无关，主题不会移除应用需要的 Lua 软件包。内核、设备功能、OpenClash 核心/订阅和实际固件更新不在主题测试范围。

## 参考与许可

- [OpenWrt 官方主题结构说明](https://github.com/openwrt/luci/wiki/HowTo:-Create-Themes)：目录、模板、静态资源和 UCI 注册。Wiki 的旧 Lua 示例已对应改成当前 LuCI ucode 模板。
- [LuCI 官方 Bootstrap ucode 模板](https://github.com/openwrt/luci/tree/master/themes/luci-theme-bootstrap/ucode/template/themes/bootstrap)：原生模板接口。`luci.js` 由系统包装模板加载一次，主题不重复加载。
- [HeroUI 官方 styles 包](https://github.com/heroui-inc/heroui/tree/main/packages/styles)：Apache-2.0，参见 `licenses/`。
- [Gravity UI Icons](https://github.com/gravity-ui/icons)：MIT；使用本地 SVG sprite，运行时不依赖图标库脚本。
- [Pin UI Thermal Dial 示例](https://www.pinui.xyz/components/thermal-dial)：状态刻度盘的视觉与代码参考，按原生 SVG/CSS 重写并移除温度调节交互。
- [Pin UI Theme Switch 示例](https://www.pinui.xyz/components/theme-switch)：外观覆盖切换的视觉参考；当前实现依照最终需求从按钮处直接展开，使用原生浏览器过渡接口。
- [GitHub 正式 Release 附件链接](https://docs.github.com/en/repositories/releasing-projects-on-github/linking-to-releases)：唯一更新清单来源，使用 `releases/latest/download/athena-release.json`。

Athena 代码采用 Apache-2.0。完整第三方许可位于 `licenses/`。
