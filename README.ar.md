[简体中文](README.md) · [English](README.en.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [العربية](README.ar.md)

<div dir="rtl" lang="ar">

# Athena v0.0.4

Athena سمة أصلية لواجهة OpenWrt LuCI، مستوحاة من HeroUI. تستخدم قوالب ucode وخدمة rpcd وواجهات JavaScript والنماذج وUCI الأصلية في LuCI. لا تتضمن بيئة تشغيل React أو أنماط Argon، ولا تحتاج إلى Node.js على جهاز التوجيه.

## الميزات

- شريط جانبي متجاوب، وجداول وعناصر إدخال مشتركة، وظلال تمرير ونوافذ حوار.
- الوضع الفاتح والداكن واتباع النظام؛ اتباع النظام هو الإعداد الأولي.
- صفحة دخول وسطية أو مقسمة، وخلفية SVG خفيفة، ولوحات زجاجية شفافة وزر لإظهار كلمة المرور.
- شعار وأيقونة موقع بصيغة PNG، ورفع صور أو فيديو للخلفية.
- التحقق من الإصدارات المستقرة والملفات، ونسخ احتياطية للاستعادة.

## التثبيت

نزّل الحزمة المناسبة من [الإصدارات](https://github.com/NXN-MAX/OpenWRT-Athena/releases)، وتحقق منها باستخدام `SHA256SUMS`. بعد نسخها إلى `/tmp`، نفّذ الأمر المناسب:

- OpenWrt 24.10 مع opkg: استخدم حزمة `.ipk`.
- OpenWrt 25.12 مع apk: استخدم حزمة `.apk`.

<div dir="ltr">

```sh
# OpenWrt 24.10
opkg install /tmp/luci-theme-athena_*.ipk
# OpenWrt 25.12
apk add --allow-untrusted /tmp/luci-theme-athena-*.apk
```

</div>

هذه حزم مبنية بصورة مستقلة باستخدام SDK، وليست موقعة بمفتاح مستودع OpenWrt الرسمي. لا تخلط بين الصيغتين. معمارية IPK هي `all` ومعمارية APK هي `noarch`. تُثبّت الاعتماديات `luci-base` و`rpcd-mod-ucode` و`ucode-mod-fs` و`ucode-mod-uci` و`curl` و`ca-bundle` من مستودعات إصدار النظام نفسه.

يُحتفظ بالملف `/etc/config/athena` والمواد المرفوعة. قبل الإزالة، انتقل إلى سمة أخرى مثبتة، ثم استخدم `opkg remove luci-theme-athena` أو `apk del luci-theme-athena`.

## الإعدادات والتحديثات

افتح **النظام ← سمة Athena** عبر `/cgi-bin/luci/admin/system/Athena-config`. ملف الإعدادات هو `/etc/config/athena`. يمكنك تحديد المظهر الافتراضي وتخطيط الدخول والمواد البصرية. يُحفظ اختيار المظهر اليدوي في المتصفح. يبقى اسم المضيف ضمن إعدادات LuCI الأصلية: **النظام ← النظام ← الإعدادات العامة**.

المصدر الوحيد للتحديث هو الملف [`athena-release.json`](https://github.com/NXN-MAX/OpenWRT-Athena/releases/latest/download/athena-release.json) المرفق بالإصدار الرسمي. لا يوجد انتقال احتياطي إلى GitHub API أو فرع المستودع أو مواقع مرآة. يظهر خطأ إذا تعذر جلب البيان أو كان غير صالح. يجري التحقق من رقم الإصدار المستقر والرابط الرسمي واسم الملف وحجمه وبصمة SHA256، ثم يُفحص الملف بعد تنزيله. لا تُثبّت إلا إصدارات مستقرة أحدث.

يستخدم المحدّث المدمج ملف `.tar.gz`، ويحفظ الإعدادات والمواد وينشئ نسخة احتياطية في `/etc/athena/backups/`. لا يغيّر سجل الإصدار لدى مدير الحزم؛ استخدم IPK/APK المناسب للترقية من خلاله. يمكن أيضًا تثبيت أرشيف مفكوك باستخدام `sh scripts/install.sh`.

## البناء والاختبارات

<div dir="ltr">

```sh
npm ci
npm run build
npm test
npm run pack
```

</div>

يستخدم البناء `@heroui/styles` لإنتاج CSS ثابت وبصمة للتخزين المؤقت. يحتوي `dist/` على الأرشيف وملف التحقق. تُنشأ حزم IPK/APK باستخدام SDK الرسمي. لا يُنشر الإصدار إلا بعد نجاح البناءين، ويُولّد البيان من الأرشيف الفعلي. يجب توحيد رقم الإصدار في `package.json` وملف القفل و`Makefile` قبل إصدار جديد.

تستخدم اختبارات الجهاز غلاف SSH يوفّره المطوّر ومسارات مؤقتة معزولة:

<div dir="ltr">

```sh
ATHENA_SSH=/path/to/device-ssh scripts/test-device.sh
ATHENA_SSH=/path/to/device-ssh python3 scripts/test-updater-device.py
```

</div>

## البنية والتوافق

توجد القوالب في `ucode/template/themes/athena/`، ومحوّل الواجهة المشترك والقائمة والإعدادات في `htdocs/luci-static/resources/`. توجد خدمة RPC في `root/usr/share/rpcd/ucode/luci.athena` وبرنامج التحديث في `root/usr/libexec/athena-update`.

بيئة التشغيل المختبرة هي OpenWrt 25.12.6 على armsr/armv8. تُبنى حزمة IPK باستخدام SDK 24.10، لكن نجاح البناء لا يعني اختبار جميع الأجهزة. لم يُختبر OpenWrt 23.05 على جهاز. يلزم دعم CSS وJavaScript الحديثين. اعتماد تطبيق خارجي على Lua مستقل عن السمة. ترقية النظام ووظائف الأجهزة ونواة OpenClash والاشتراكات خارج نطاق اختبارات السمة.

## الترخيص والمراجع

الترخيص Apache-2.0؛ راجع [LICENSE](LICENSE) و[NOTICE](NOTICE) و[تراخيص الأطراف الأخرى](licenses/). المراجع: [بنية سمات LuCI](https://github.com/openwrt/luci/wiki/HowTo:-Create-Themes)، و[HeroUI](https://github.com/heroui-inc/heroui)، و[Gravity UI Icons](https://github.com/gravity-ui/icons)، ومثالا Thermal Dial وTheme Switch من Pin UI. لا تُرسل تطبيقات React لهذه الأمثلة إلى جهاز التوجيه.

</div>
