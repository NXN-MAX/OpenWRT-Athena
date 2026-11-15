'use strict';
'require view';
'require form';
'require rpc';
'require uci';
'require ui';
'require athena.ui as widgets';
const callGet=rpc.declare({object:'luci.athena',method:'get',expect:{'':{}}});
const callInstall=rpc.declare({object:'luci.athena',method:'install',params:['kind','token'],expect:{'':{}}});
const callRemove=rpc.declare({object:'luci.athena',method:'remove',params:['kind','name'],expect:{'':{}}});
const callSelect=rpc.declare({object:'luci.athena',method:'select',params:['name'],expect:{'':{}}});
const checkUpgrade=rpc.declare({object:'luci.athena',method:'check_update',expect:{'':{}}});
const startUpgrade=rpc.declare({object:'luci.athena',method:'start_update',params:['tag'],expect:{'':{}}});
const upgradeStatus=rpc.declare({object:'luci.athena',method:'update_status',params:['job'],expect:{'':{}}});
const zh=document.documentElement.lang.startsWith('zh');
const t=(cn,en)=>zh?cn:en;
const base='/luci-static/athena/branding/';
const nativeButton=(label,variant,handler,disabled)=>E('button',{type:'button',class:`button button--${variant} button--sm`,click:handler,disabled:disabled||null},label);
function checked(result){if(result.result!==0)throw new Error(result.error||_('Unknown error'));return result;}
function errorMessage(error){ui.addNotification(null,E('p',{},error.message),'error');}
function token(){const data=new Uint8Array(16);crypto.getRandomValues(data);return [...data].map(value=>value.toString(16).padStart(2,'0')).join('');}
function upgradeError(error){
 const messages={
  'GitHub API rate limit; try again later':'GitHub 请求次数已达上限，请稍后再试。',
  'curl is required for GitHub updates':'请安装 curl 和 ca-bundle 后检查更新。',
  'Invalid GitHub response':'GitHub 返回了无法识别的版本信息。',
  'Invalid stable release':'GitHub 发布版本信息无效。',
  'No matching newer release. Check for updates again.':'没有匹配的新版本，请重新检查更新。',
  'Not enough free space for update and rollback backup':'空间不足，无法同时保存更新包和回滚备份。',
  'A theme update is already running':'主题更新正在进行，请稍候。'
 };
 if(zh&&messages[error.message])return messages[error.message];
 if(zh&&error.message.startsWith('Cannot reach GitHub releases'))return '暂时无法连接 GitHub，请稍后重试。';
 return error.message;
}
return view.extend({
 load:function(){return Promise.all([uci.load('athena'),callGet()]);},
 render:function(data){
  this.readonly=!L.hasViewPermission();this.assets=checked(data[1]);
  const map=new form.Map('athena',t('Athena主题','Athena Theme'),t('管理主题外观、登录页素材与版本更新。','Appearance, login assets and theme updates.'));
  const updates=map.section(form.NamedSection,'global','global');
  updates.render=()=>this.upgradeRoot;
  const section=map.section(form.NamedSection,'global','global',t('外观','Appearance'));
  let option=section.option(form.Value,'primary',t('主题色','Primary color'));
  option.placeholder='#1672ee';option.rmempty=false;
  option.validate=function(section,value){return /^#[0-9a-f]{6}$/i.test(value)||t('请输入六位十六进制颜色，例如 #1672ee','Use a six-digit hex color, e.g. #1672ee');};
  option=section.option(form.ListValue,'default_mode',t('默认外观模式','Default appearance'),t('未手动选择时使用此模式；右上角的选择会记在当前浏览器。','Used until a mode is chosen manually. The top-right choice is remembered in this browser.'));
  option.value('system',t('跟随系统','Follow system'));option.value('dark',t('暗黑模式','Dark mode'));option.value('light',t('日光模式','Light mode'));option.default='system';option.rmempty=false;
  option=section.option(form.ListValue,'login_style',t('登录页布局','Login layout'));
  option.value('classic',t('分栏','Split'));option.value('centered',t('居中','Centered'));option.default='classic';option.rmempty=false;
  this.assetRoot=E('div',{},[]);this.renderAssets();
  this.upgradeRoot=E('div');this.renderUpgrade();
  upgradeStatus('').then(result=>{if(result.result===0&&result.job&&!['idle','complete','failed','rolled_back','rollback_failed'].includes(result.phase))this.watchUpgrade(result.job);}).catch(()=>{});
  return map.render().then(node=>E('div',{},[node,this.assetRoot]));
 },
 renderUpgrade:function(){
  const release=this.release,busy=this.upgradeBusy;
  const messages={unreleased:t('GitHub 暂无正式发布版本。','No stable GitHub release has been published.'),current:t('当前已是最新版本。','You are up to date.'),available:t('有新版本可更新。','A new version is available.'),missing_asset:t('新版本尚未提供可校验的主题安装包。','The release has no verified theme archive.')};
  const check=nativeButton(busy?t('检查中…','Checking…'):t('检查更新','Check for updates'),'secondary',event=>{
   this.upgradeBusy=true;this.upgradeError=null;this.updateMessage=null;this.renderUpgrade();return checkUpgrade().then(checked).then(result=>{this.release=result;}).catch(error=>{this.release=null;this.upgradeError=upgradeError(error);}).finally(()=>{this.upgradeBusy=false;this.renderUpgrade();});
  },busy||this.installing);
  const update=nativeButton(t('在线更新','Update theme'),'primary',()=>this.confirmUpgrade(),this.readonly||this.installing||busy||!release?.available);
  this.upgradeRoot.replaceChildren(widgets.card(E('h3',{},t('主题更新','Theme update')),[
   E('p',{},t('当前版本：','Current version: ')+'v'+(this.assets.version||'0.0.1')),
   E('p',{},release?.latest?t('最新版本：','Latest version: ')+'v'+release.latest:t('从 GitHub 正式发布版本检查更新。','Check stable releases from GitHub.')),
   this.upgradeError?E('p',{role:'alert'},this.upgradeError):E('p',{},this.updateMessage||messages[release?.status]||''),
   E('div',{class:'athena-upload-actions'},[check,update,E('a',{class:'button button--ghost button--sm',href:'https://github.com/NXN-MAX/OpenWRT-Athena/releases',target:'_blank',rel:'noopener noreferrer'},t('发布记录','Releases'))])
  ]));
 },
 confirmUpgrade:function(){
  const release=this.release;if(!release?.available||this.installing||this.readonly)return;
  ui.showModal(t('更新 Athena 主题','Update Athena theme'),[
   E('p',{},'v'+this.assets.version+' → v'+release.latest),
   E('p',{},t('更新前会备份当前主题，保留主题设置和已上传素材。','The current theme is backed up before updating. Settings and uploaded assets are preserved.')),
   E('div',{class:'right'},[nativeButton(_('Cancel'),'tertiary',ui.hideModal),nativeButton(t('更新','Update'),'primary',event=>{
    const button=event.currentTarget;button.disabled=true;
    return startUpgrade(release.tag).then(checked).then(result=>{ui.hideModal();this.watchUpgrade(result.job);}).catch(error=>{button.disabled=false;errorMessage(new Error(upgradeError(error)));});
   })])
  ]);
 },
 watchUpgrade:function(job){
  clearTimeout(this.upgradeTimer);this.installing=true;this.upgradeError=null;
  const phases={starting:t('准备更新…','Preparing update…'),downloading:t('正在下载发布包…','Downloading release…'),verifying:t('正在校验发布包…','Verifying release…'),installing:t('正在安装主题…','Installing theme…'),complete:t('更新完成，重新加载页面后生效。','Update complete. Reload the page.'),failed:t('更新失败，当前主题未更改。','Update failed. The current theme was not changed.'),rolled_back:t('更新失败，已恢复更新前的主题。','Update failed. The previous theme was restored.'),rollback_failed:t('恢复未完成，请使用主题备份恢复。','Restore is incomplete. Use the theme backup.')};
  let failures=0;
  const tick=()=>upgradeStatus(job).then(checked).then(result=>{
   failures=0;this.updateMessage=phases[result.phase]||phases.starting;
   const done=['complete','failed','rolled_back','rollback_failed'].includes(result.phase);this.installing=!done;
   if(result.phase==='complete'){this.assets.version=result.version;this.release=null;}
   if(result.backup)this.updateMessage+=t(' 备份：',' Backup: ')+result.backup;
   this.renderUpgrade();if(!done)this.upgradeTimer=setTimeout(tick,1500);
  }).catch(error=>{if(++failures<5)this.upgradeTimer=setTimeout(tick,2000);else{this.installing=false;this.upgradeError=upgradeError(error);this.renderUpgrade();}});
  this.renderUpgrade();tick();
 },
 update:function(result){this.assets=checked(result);this.renderAssets();},
 act:function(button,work){button.disabled=true;return Promise.resolve().then(work).then(result=>this.update(result)).catch(errorMessage).finally(()=>{if(button.isConnected)button.disabled=this.readonly;});},
 upload:function(kind,event){
  const button=event.currentTarget;const id=token();button.disabled=true;
  return ui.uploadFile('/tmp/athena-upload-'+id+'.tmp',button).then(file=>{if(!file)return;return callInstall(kind,id).then(result=>{this.update(result);ui.addNotification(null,E('p',{},t('素材已更新，重新加载页面后生效。','Asset updated. Reload the page to apply.')),'info');});}).catch(errorMessage).finally(()=>{if(button.isConnected)button.disabled=this.readonly;});
 },
 remove:function(kind,name){
  ui.showModal(t('移除素材','Remove asset'),[E('p',{},kind==='background'?t('移除这个背景文件？','Remove this background file?'):t('恢复默认图标？','Restore the default icon?')),E('div',{class:'right'},[
   nativeButton(_('Cancel'),'tertiary',ui.hideModal),nativeButton(_('Remove'),'danger-soft',event=>this.act(event.currentTarget,()=>callRemove(kind,name||'')).then(()=>ui.hideModal()))
  ])]);
 },
 renderAssets:function(){
  const value=this.assets;const readonly=this.readonly;
  const cards=[['logo',t('自定义图标','Custom logo'),t('PNG，16–1024 像素，最大 1 MiB。保留图片比例显示。','PNG, 16–1024 pixels, up to 1 MiB. Aspect ratio is preserved.')],['favicon',t('浏览器图标','Browser icon'),t('正方形 PNG，16–1024 像素，最大 1 MiB。','Square PNG, 16–1024 pixels, up to 1 MiB.')]].map(([kind,title,description])=>E('section',{class:'athena-upload-card'},[
   E('h3',{},title),E('p',{},description),E('div',{class:'athena-icon-preview'},E('img',{src:value[kind]?base+value[kind]:'/luci-static/athena/logo.svg',alt:title})),E('div',{class:'athena-upload-actions'},[
    nativeButton(t('上传 PNG','Upload PNG'),'primary',event=>this.upload(kind,event),readonly),nativeButton(t('恢复默认','Reset'),'secondary',()=>this.remove(kind,''),readonly||!value[kind])
   ])
  ]));
  const rows=(value.files||[]).map(file=>{const selected=value.background===file.name;const video=/\.(mp4|webm)$/.test(file.name);return E('tr',{class:'tr'},[
   E('td',{class:'td'},video?E('span',{},'VIDEO'):E('img',{class:'athena-file-preview',src:base+file.name,alt:''})),
   E('td',{class:'td'},[E('span',{},file.name.slice(0,15)+'…'+file.name.slice(file.name.lastIndexOf('.'))),selected?E('small',{class:'athena-file-active'},t('当前使用','In use')):'']),
   E('td',{class:'td'},`${(file.size/1048576).toFixed(2)} MiB`),E('td',{class:'td cbi-section-actions'},E('div',{class:'button-group button-group--sm'},[
    nativeButton(selected?t('已选用','Selected'):t('使用','Use'),'secondary',event=>this.act(event.currentTarget,()=>callSelect(file.name)),readonly||selected),nativeButton(_('Delete'),'danger-soft',()=>this.remove('background',file.name),readonly)
   ]))
  ]);});
  if(!rows.length)rows.push(E('tr',{class:'tr placeholder'},E('td',{class:'td',colspan:4},t('还没有上传背景。','No backgrounds uploaded.'))));
  const table=E('table',{class:'table','aria-label':t('背景文件','Background files')},[E('tr',{class:'tr table-titles'},[t('预览','Preview'),t('文件','File'),t('大小','Size'),_('Actions')].map(label=>E('th',{class:'th'},label))),...rows]);
  const background=widgets.card(E('h3',{},t('上传背景','Backgrounds')),[
   E('p',{},t('登录页使用本地图片或视频。支持 JPG、PNG、GIF、WebP、MP4、WebM，单个文件最大 20 MiB。','Local login background. JPG, PNG, GIF, WebP, MP4 or WebM, up to 20 MiB per file.')),
   E('div',{class:'athena-upload-actions'},[nativeButton(t('上传背景','Upload background'),'primary',event=>this.upload('background',event),readonly),E('span',{class:'athena-metric-detail'},t('可用空间：','Available space: ')+(value.available/1048576).toFixed(1)+' MiB')]),table
  ]);
  this.assetRoot.replaceChildren(E('div',{class:'athena-config-grid'},cards),background);
 }
});
