# LuCI 官方收录准备

候选目标为 `openwrt/luci` 的 `master`，包目录为 `themes/luci-theme-athena`。
自有签名源与官方收录是两条独立发布渠道；创建 fork 或 PR 不表示已经获得官方收录。

## 候选版的调整

- 使用标准 `../../luci.mk`，声明维护者、依赖、Apache-2.0/MIT 许可与配置保留路径。
- 保留原生 ucode 模板、素材 RPC、LuCI JavaScript 控件和 UCI 保存/应用行为。
- 移除 GitHub 归档更新器、更新任务 RPC/ACL 和 curl/CA 依赖。更新入口读取实际菜单，兼容 `package-manager` 与 `opkg`；没有软件管理应用时不生成无效链接。
- 不携带自有源配置或公私钥。软件包由 OpenWrt 构建、签名并通过其包管理器维护。
- 安装只注册 Athena，不覆盖管理员选中的主题；卸载只删除自己的主题注册。
- 使用 LuCI gettext 与初始 POT；后续翻译交给 OpenWrt Weblate，不向官方分支复制独立版的双语判断。
- SDK 直接使用仓库中的预构建 CSS。CSS 开发源码置于 `style-src/`，避免 LuCI 将 `src/` 误判为需要执行原生 `make install` 的目录。
- 仅对本包关闭旧式 CSS 压缩和 ucode 模板预编译，不覆盖全局构建配置。
- 保留完整第三方许可与模板来源说明；不把 README 截图、上传素材或 Node.js 依赖打入设备包。

## 生成与审查

在电脑上准备官方 LuCI checkout，并切换到独立的功能分支。目标包目录必须为空：

```sh
python3 scripts/prepare-upstream.py /path/to/luci/themes/luci-theme-athena
```

LuCI 自身的 ESLint 原先仅排除仓库根目录的 package-lock.json。为保留主题开发依赖的锁文件，候选补丁将该排除规则扩展为 `**/package-lock.json`；这是开发检查配置，不影响设备构建或运行。生成后可在 LuCI checkout 执行 `git apply /path/to/Athena/doc/upstream-eslint.patch`。

在 LuCI checkout 中生成翻译模板：

```sh
mkdir -p themes/luci-theme-athena/po/templates
./build/i18n-scan.pl themes/luci-theme-athena > themes/luci-theme-athena/po/templates/athena.pot
```

可选开发环境下，安装锁定依赖后运行 `npm run build`、`npm test`。
JavaScript 可用 Prettier 3.6.2 的 tab/single-quote/no-trailing-comma 配置整理，再使用 LuCI 自身 ESLint 规则检查。
设备包构建不需要 npm。生成器不会提交、代签、推送、安装候选包或改动独立发行版。

## 已验证的范围

- 独立发行版：57 项界面/源码回归，3 组签名索引单元测试。
- 自有源：14 项原生设备检查，包括公开下载回验、原生 apk 解析索引及获取包、错误密钥/篡改拒绝、重复启用和原有源保留。
- 官方候选版：45 项 DOM/模式/状态/设置回归，16 项隔离素材 RPC 检查。
- 在 OpenWrt 25.12.6、armsr/armv8 VM 上编译所有模板与 RPC，并隔离测试注册和卸载行为。
- LuCI 自身 ESLint 检查候选 JavaScript、ACL/menu JSON 与 README 无错误。
- [官方 SDK 构建结果](https://github.com/NXN-MAX/OpenWRT-Athena/actions/runs/45021572695)：OpenWrt 24.10.4 IPK、25.12.6 APK 均成功。

SDK 构建通过不代表已在 24.10 设备上完成运行测试，也不代表官方 master 的全部应用和第三方插件都已验证。初始 gettext 模板尚需官方 Weblate 接入；候选包未替换现有开发 VM 的运行主题。

## 提交前的声明

[LuCI 贡献规范](https://github.com/openwrt/luci/blob/master/CONTRIBUTING.md)要求每个提交使用真实姓名、非 GitHub noreply 邮箱，并包含 Signed-off-by。
已提供的维护者信息为 `ZHICHENG CHEN <czhic1996@gmail.com>`。添加该声明前，仍需维护者明确确认有权按 [DCO](https://developercertificate.org/)贡献代码及素材；姓名和邮箱本身不代替该确认。

Git 提交的加密签名、DCO 的 Signed-off-by，以及软件源包签名是不同机制。官方机器人会对未验证的 Git 提交签名给出警告；这不会被 Athena 的软件源签名替代。

确认 DCO 后，使用本地功能分支创建带正文的提交，再添加 Signed-off-by 并推送到自己的 LuCI fork。PR 应指向 `openwrt/luci:master`；当前只准备候选代码与说明，尚未声明被官方接纳。
