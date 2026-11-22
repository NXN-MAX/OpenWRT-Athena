include $(TOPDIR)/rules.mk
LUCI_PKGARCH:=all
LUCI_URL:=https://github.com/NXN-MAX/OpenWRT-Athena
LUCI_MAINTAINER:=NXN-MAX
LUCI_TITLE:=Athena native HeroUI theme
LUCI_DEPENDS:=+luci-base +rpcd-mod-ucode +ucode-mod-fs +ucode-mod-uci +curl +ca-bundle
PKG_VERSION:=0.0.6
PKG_RELEASE:=1
PKG_LICENSE:=Apache-2.0
LUCI_MINIFY_UT:=0
CONFIG_LUCI_UTMIN:=
CONFIG_LUCI_CSSTIDY:=
define Package/luci-theme-athena/conffiles
/etc/config/athena
endef
# Run npm ci && npm run build before compiling with the OpenWrt SDK.
ifneq ($(wildcard ../../luci.mk),)
include ../../luci.mk
else
include $(TOPDIR)/feeds/luci/luci.mk
endif

# call BuildPackage - OpenWrt buildroot signature
