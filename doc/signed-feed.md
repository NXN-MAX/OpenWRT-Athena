# Athena 签名软件源

这是 Athena 自有的第三方源，不是 OpenWrt 官方源。只发布 `luci-theme-athena`；设备的固件和依赖继续来自原有官方软件源。不要跨固件版本混用源。

| 固件 | 管理器 | 仓库 |
| --- | --- | --- |
| OpenWrt 24.10.x | opkg / IPK | `https://raw.githubusercontent.com/NXN-MAX/OpenWRT-Athena/feeds/24.10/all` |
| OpenWrt 25.12.x | apk / APKv3 | `https://raw.githubusercontent.com/NXN-MAX/OpenWRT-Athena/feeds/25.12/noarch/packages.adb` |

## 首次启用

先检查本页的公钥指纹，再下载并阅读安装脚本。脚本只添加 Athena 公钥和源配置，不安装软件、不关闭签名验证、不修改原有官方源。

```sh
curl -fL https://raw.githubusercontent.com/NXN-MAX/OpenWRT-Athena/main/scripts/enable-feed.sh -o /tmp/athena-feed.sh
less /tmp/athena-feed.sh
sh /tmp/athena-feed.sh
```

OpenWrt 25.12：

```sh
apk update
apk add luci-theme-athena
```

OpenWrt 24.10：

```sh
opkg update
opkg install luci-theme-athena
```

启用源后，通过 LuCI 软件管理或对应包管理器更新主题。不要同时使用主题内置的归档覆盖更新来管理同一份包；归档安装不会同步包管理器版本记录。原有 GitHub Release 安装包保持不变，签名源中的 APK 是对同一份发布内容重新签名的副本，文件哈希因此不同。

## 公钥与指纹

- opkg usign 指纹：`efe004bab7c083b3`。
- [opkg 公钥](../keys/athena-opkg.pub)文件 SHA256：`f54629556f98e848b5e8b04ad7b53c730bed33ce22da7591c70d24bcc1f178da`。
- [APK 公钥](../keys/athena-apk.pub.pem)文件 SHA256：`6fc101f3c59dd1a98a1f3e172eb768f79e1298d1e09b9ec0bd34874b8aee3420`。

安装脚本固定核对公钥文件 SHA256，已有同名但不同的 key 或配置时会拒绝覆盖。首次从 HTTPS 获取脚本仍然是初始信任步骤；应从已信任的项目渠道核对指纹。公钥变更需明确的密钥轮换流程，发布器不会自动替换已有源的公钥。

## 发布者流程

签名私钥保存在维护者本机的 `~/.config/athena/signing/`，权限 0600，目录权限 0700。私钥不进入 Git、GitHub Actions、Release 或设备安装包，应另做加密离线备份。

准备从对应 Release 下载的 IPK、APK 和 `SHA256SUMS`。签名主机需要 `usign` 及包含 `adbsign`、`mkndx` 的完整 APKv3 工具；OpenWrt 路由器上的精简 apk 往往不包含这两个发布命令。工具可来自官方 OpenWrt SDK。`--ssh` 指向维护者自己的可信签名主机包装命令，不能提交其 SSH 私钥。

```sh
python3 scripts/publish-feed.py /path/to/release /path/to/new-signed-feed \
  --version 0.0.6 --ssh /path/to/signing-host-ssh \
  --apk-tool /path/on/signing/host/to/full-apk

# 审阅并验证结果后，再增加 --publish 发布到 feeds 分支。
```

流程核对原始发布包哈希和包名/版本/架构，签署 opkg 索引、独立 APK 与 APK 索引，并用公钥重新验证。临时私钥仅通过 SSH 传输，在签名结束时清理；返回的归档只包含公开文件。发布使用正常 Git SSH 推送，不覆盖 main、不强推，保留旧包文件供缓存索引使用。

GitHub Actions 继续构建与验证 Release；签名发布由持有私钥的维护者在本机执行。因此后续 Release **不会自动进入签名源**，需要执行上述签名发布步骤。当前不将长期私钥存入 CI，以免产生隐含的密钥托管授权。

## 验证与移除

测试必须覆盖正确签名可用、错误公钥拒绝、索引/包篡改拒绝、重复启用无重复配置，以及不受支持固件被拒绝。

```sh
python3 -m unittest discover -s tests -p 'test_feed.py'
python3 scripts/test-feed-device.py /path/to/signed-feed --ssh /path/to/test-device-ssh
```

设备测试仅写入随机命名的 `/tmp/athena-feed-test-*`，不改动实际安装的主题、公钥或源配置；结束时自动清理。24.10 的索引经原生 usign 验证；25.12 的软件包与索引经原生 apk 验证。本轮没有在 24.10 设备上执行实际 opkg 安装。

移除源：删除 APK 的 `/etc/apk/repositories.d/athena.list`，或仅删除 opkg `customfeeds.conf` 中以 `src/gz athena ` 开头的行；确认没有其他用途后再移除对应 Athena 公钥。不会自动卸载已安装主题。卸载主题前，先切换到另一个已安装主题。
