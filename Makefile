include $(TOPDIR)/rules.mk
LUCI_TITLE:=Athena native HeroUI theme
LUCI_DEPENDS:=+luci-base +rpcd-mod-ucode +ucode-mod-fs +ucode-mod-uci +curl +ca-bundle
PKG_VERSION:=0.0.2
PKG_RELEASE:=1
PKG_LICENSE:=Apache-2.0
LUCI_MINIFY_UT:=0
CONFIG_LUCI_UTMIN:=
CONFIG_LUCI_CSSTIDY:=
PKG_CONFFILES:=/etc/config/athena
# Run npm ci && npm run build before compiling with the OpenWrt SDK.
ifneq ($(wildcard ../../luci.mk),)
include ../../luci.mk
else
include $(TOPDIR)/feeds/luci/luci.mk
endif
