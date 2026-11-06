# 原生门户目录浏览修复

问题：demo1 有独立报表 Browser，但根目录和上级目录的 Browser 被目录授权同步移除，原生门户首页和文件夹 CatalogItems 返回403。认证成功，不属于 RLS 错误。

修复 demo_admin.Policies.replace_selection：将资源选择与必需的祖先导航分开计算。对已授权目录/报表补充根目录与祖先目录 Browser；未选中的继承子项先解除继承并保留所有现有成员，再授予上级导航，避免现有报表扩权。现有目录/报表选择不改动。撤销和停用仍按同一套计算清理。沿用既有60秒同步机制。

注意：原生 Browser 同时包含目录和报表查看任务。新增在导航祖先下并默认继承的报表，在下一次60秒核对前可能继承到导航 Browser。正式接入须使用只含 View folders 的专用导航角色，或发布时先设置独立策略再开放访问。本次尝试原生 SOAP CreateRole 返回现有 rsAuthorizationExtensionError，未创建角色，未修改 FullTrust。当前修复已验证所有现存报表访问矩阵不变，不能将此验证扩大为无同步窗口的发布安全保证。

验证：4项目录策略测试、10项RLS测试通过；三个账号 Home浏览200，所有现存报表身份权限矩阵和授权选择不变。RLS跨报表批量授权回归通过并恢复原分配。浏览器 demo1 登录、主页目录、P6_RLS_Demo目录正常。后台没有使用 Windows Administrator 代替普通用户访问报表。

服务器代码备份：C:\ProgramData\P4DemoApp\portal-nav-backup-20261105-040808。仅更新 demo_admin.py，未改账号密码、RLS规则、安全扩展或 FullTrust。
