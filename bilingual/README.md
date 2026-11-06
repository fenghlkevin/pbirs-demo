# Português (Angola) / 中文

共享 Demo：http://pbirs.example.internal:8765/ 。默认 pt-AO，顶部切换中文。语言保存在 P4DemoLang Cookie（同主机跨端口共享），URL lang 参数可指定初始语言，切换时同步更新 URL，刷新保留偏好。

已覆盖 Demo 登录、用户管理、目录授权、RLS 用户批量授权、弹窗、状态和常见接口错误。语言切换保留当前授权选择和 RLS 草稿，不触发权限写入。用户名、业务姓名、资源路径和模型角色标识仍使用原数据。内嵌报表格式参数按选择传 pt-AO / zh-CN，代理请求在葡语下使用 PBIRS 已内置的 pt-BR UI 资源。按语言区分静态代理缓存，避免语言资源交叉。

PBIRS 自定义登录页：http://pbirs.example.internal/ReportServer/P4Login.aspx ，支持 ?lang=pt-AO / ?lang=zh-CN。表单、错误提示、当前身份及登录后回跳提示均已双语。沿用既有 CSRF、HMAC认证接口、票据验证及安全返回地址。正式部署仅更新正在使用的 P4Login.aspx，未新增旧 P4Portal.aspx。

PBIRS 原生门户与报表正文不属于本次自定义页面翻译：原生门户受微软已安装语言资源及浏览器语言影响，没有修改微软产品静态文件。报表内固定标题、字段名等仍需报表作者提供模型或报表翻译，不能由 Demo 语言开关自动翻译。

部署仅更新 server.py、index.html、bilingual/translations.json、PBIRS P4Login.aspx。账号、密码、资源授权、RLS成员与规则未改；未部署DLL，也未修改 FullTrust / web.config / rsreportserver.config / rssrvpolicy.config，部署时核对配置哈希不变。服务器备份 C:\ProgramData\P4DemoApp\bilingual-backup-20261105-042441；后续 index.html 翻译补丁在服务器 app 目录应用。

验证：17 项既有测试通过；verify.py 对 pt-AO / zh-CN 原生表单登录、CSRF拒绝、当前用户身份、门户目录、API错误本地化进行验证，RLS成员列表前后一致。浏览器确认葡语用户管理和RLS列表、中文切换、未保存RLS勾选保留、语言偏好刷新保留。截图 users-pt.png、rls-pt.png。

build.py 和 localize_login.py 是本次迁移脚本，不应对已迁移文件重复运行。后续翻译直接编辑 index.html 的 PT 字典、静态 data-i18n 标记及 translations.json；两份字典需同步。
