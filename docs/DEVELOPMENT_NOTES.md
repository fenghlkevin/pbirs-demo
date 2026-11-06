# P4 用户身份与 Power BI Report Server 演示

## 当前可用入口

- 局域网原生门户：[http://pbirs.example.internal/Reports](http://pbirs.example.internal/Reports)
- 统一登录页：[http://pbirs.example.internal/ReportServer/P4Login.aspx](http://pbirs.example.internal/ReportServer/P4Login.aspx)
- 本机嵌入演示：[http://127.0.0.1:8765/](http://127.0.0.1:8765/)

原生门户使用浏览器自身的 PBIRS Forms Cookie；不要求客户端运行本机 Demo。登录页与一次性票据回调合并在配置的登录入口，不新增服务器端口、服务或防火墙规则。

| 系统账号 | PBIRS 身份 | 权限 |
|---|---|---|
| demo1 | p4:demo1 | Report_A |
| demo2 | p4:demo2 | Report_B |
| demo3 | p4:demo3 | Report_A、Report_B |
| p4admin | p4:portaladmin | 独立系统管理员 |

普通账号密码见本机 `app-logins.local.json`；管理员密码见 `admin-login.local.json`。文件权限均为 600，已排除 Git。没有使用 Windows Administrator 代替用户查看报表，也不读取 Windows 用户密码。

## 本轮登录报错修复

原错误是扩展按默认 .NET 4 安全透明性规则加载，与 PBIRS 的 RosettaSrv/legacy CAS 宿主不兼容，导致已经携带 Forms Cookie 的 ReportServer 回调出现 `Inheritance security rules violated`。

仅修改扩展程序集的兼容性声明为 `SecurityRules(SecurityRuleSet.Level1)`，并移除不匹配的显式 SecurityCritical 标注。隔离 AppDomain 测试确认该实现可加载，同时 `FullyTrusted=False`，越界文件 IO 仍被 CAS 拒绝。替换了 ReportServer/bin、Portal、PowerBI 三处 DLL。

**没有修改 FullTrust 配置。** 以下三个文件在本轮修复前后 SHA-256 相同：

| 配置文件 | SHA-256 |
|---|---|
| rssrvpolicy.config | 30B031FFB1EF2465B6BE45EFCA461C6C8B498F1021CF2A148A2B87EE23978432 |
| web.config | DFD1980F7FBD41DF290627C1BC70DC3C1E291F66221E3013BA98A70CCEEA230B |
| rsreportserver.config | C32E492BA55FAA45E82D8E40962590070F31D2EBC7108BBA112E8738014749CC |

没有新增 P4 FullTrust 代码组，也没有部署此前准备的强名称签名/信任方案。备份位置记录于服务器 `C:\ProgramData\P4PbirsDemo\compat-backup-path.txt`，本轮备份目录为 `compat-backup-20261104-195123`。

## 验证结果和限制

已通过：

- `verify_browser_portal.py`：四账号原生网页登录、浏览器身份、普通用户目录与资源权限、管理员创建/删除临时文件夹、已登录回调、报表深链接、安全回跳、CSRF 拒绝。
- `verify_permissions.py`：三个普通 P4 身份的目录、报表元数据与模型权限矩阵。
- `verify_tickets.py`：签名篡改、过期、重放、错误 issuer/audience、未来时间、新 P4 身份无需 Windows 用户但默认无报表权限。
- 浏览器验收：p4admin 主页目录、站点设置、文件夹属性管理，以及 Report_A、Report_B 的原生图表和明细。

仍有限制：额外的旧 SOAP `ReportService2010.GetItemType` 检查返回 `rsAuthorizationExtensionError` / SecurityException。本轮未通过增加权限处理这个独立的 SOAP 限制；不能将当前 Power BI 门户验收结果推广为所有旧 SSRS/SOAP 操作均可用。对应检查脚本为 `admin-fix/verify_soap.py`，该脚本当前未通过。

此前将整个原生网页登录问题直接判断为“必须增加 FullTrust”不准确；当前门户流程已通过代码兼容性修复恢复。

## 身份链路

系统账号验证（PBKDF2-SHA256）→ 服务端取得稳定 P4 subject → HMAC-SHA256 一次性票据 → PBIRS 登录页验签和 claims 检查 → 原子 nonce 记录拒绝重放 → 建立 PBIRS Forms Cookie → 按角色 ACL 执行资源权限。

票据默认有效期 30 秒，绑定 issuer、audience、subject、iat、exp 和随机 jti。原生浏览器票据通过隐藏 POST 表单提交，不放入 URL；仅允许跳回本服务器 `/Reports` 路径。普通用户默认进入演示文件夹，管理员进入门户根目录。

- `p4:maintenance` 仅供部署脚本配置授权，不向演示登录界面提供。
- `p4:portaladmin` 是明确创建的独立系统管理员身份，不是 Windows/AD 账号。
- 自定义授权扩展使用禁止 DTD 的 XML ACL，不使用 BinaryFormatter。

## 文件与启动

- `server.py`、`index.html`：本机目录/iframe Demo及原生门户票据按钮。
- `ticket_auth.py`：票据签发和后端 PBIRS 会话建立。
- `custom-security/P4Security.cs`：认证、资源授权与宿主兼容性实现。
- `custom-security/P4Login.aspx`：共享系统登录、票据验证和浏览器回跳。
- `app-accounts.local.json`：系统密码哈希及 subject。
- `ticket-signing.local.json`：签名密钥，仅本机服务端读取，权限 600。

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python server.py
```

共享登录页现通过本机回环接口调用部署在服务器上的 Demo 账号库。旧 `C:\ProgramData\P4PbirsDemo\system-users.json` 仅保留历史备份，登录不再读取它。

## 回滚与后续

本轮仅 DLL 回滚：停止 PowerBIReportServer 服务，将 compat 备份中的 DLL 复制回 ReportServer/bin、Portal、PowerBI，然后启动服务。可通过现有 Windows 维护通道执行，不修改信任配置。

更早的原始 NTLM 配置备份仍由 `backup-path.txt` 保留，完整恢复步骤为执行服务器 `rollback.ps1` 后，运行本机 `custom-security/restore_original_policies.py` 恢复演示资源的原策略。未经用户要求不要执行此完整回滚。

当前是独立 Demo，尚未修改 P4 正式 Keycloak/IAM。新增静态 RLS 测试报表见 rls-demo/README.md，已验证三个 Demo 身份的不同数据范围。正式集成应使用现有认证上下文和 IAM 业务授权，不保留另一套用户密码副本。测试环境使用 HTTP；生产部署需要 HTTPS、受控密钥管理、nonce 清理/共享存储及会话撤销设计。原生 Forms Cookie 的有效期为一小时，退出本机 Demo 不等同于撤销所有原生浏览器会话。

## Demo 用户管理与报表授权

管理界面位于我们自己的共享 Demo：`http://pbirs.example.internal:8765/`，不是 PBIRS 门户中的用户管理界面。

新增 `admin` 账号，密码见本机 `demo-admin-login.local.json`（权限 600）。它是 Demo 管理员，报表查看身份为 `p4:admin`；不等同于原生 PBIRS 的全局管理员 `p4admin`。

- 用户管理：新建普通用户、启用/停用、重置密码。新账号默认无报表权限；密码只保存加盐 PBKDF2 哈希。管理员账号受保护。
- 报表授权：选择普通用户，勾选 Report_A、Report_B 的查看权限，保存或取消。当前支持 PBIRS 完整目录树中的文件夹、Power BI 报表和分页报表；只修改正在管理用户的查看角色，保留其他用户及维护身份的授权。
- 所有管理操作均由后端校验 Demo 管理员角色，普通用户调用管理 API 返回 403，不只是隐藏按钮。
- 保存授权会真正更新 PBIRS 中该用户的 Browser 资源策略，并在有报表授权时授予对应目录浏览权限。修改单个用户时保留其他用户和维护身份的策略。多步骤写入失败时补偿回滚。
- 停用用户会使其 Demo 会话失效，并撤销演示目录的报表权限；重新启用恢复原授权。重置密码会使原 Demo 会话失效，但不宣称撤销 PBIRS 已签发的所有 Forms Cookie。
- 授权控制平面使用仅在受保护管理接口内建立的 `p4:maintenance` 服务身份。普通报表列表、图表查询和原生门户票据仍使用实际登录用户的 subject，从不使用维护身份代替查看。
- 新建用户既可登录 Demo，也可在 PBIRS 登录页输入相同账号密码。PBIRS 通过签名回环 API 验证账号，不复制密码哈希，不创建 AD 用户。

新增源码 `demo_admin.py`，管理 API 位于 `/api/admin/`。`verify_admin.py` 已覆盖：新建账号默认拒绝、客户端伪造角色/subject 无效、授权/撤销在 PBIRS 生效、停用与恢复、密码重置、管理员保护、错误报表 ID 拒绝，以及第二次远程策略写入失败时的补偿回滚和其他用户策略保持。

验收保留了一个“授权验证用户”，登录信息见 `demo-review-login.local.json`；可用它测试普通用户体验。原 demo1/demo2/demo3 回归验证通过。本轮未修改 PBIRS 认证扩展、登录页面或 FullTrust 配置。


## 同服务器统一认证部署（2026-11-05）

- Demo：http://pbirs.example.internal:8765/；PBIRS：http://pbirs.example.internal/Reports。
- 服务器代码：`C:\ProgramData\P4DemoApp\app`；唯一活动账号库：`C:\ProgramData\P4DemoApp\data\app-accounts.local.json`。本机工作区账号文件是部署时快照，后续以服务器管理页面为准。
- Python 3.13.9 独立运行时位于 runtime，计划任务 P4DemoApp 以 NETWORK SERVICE 启动，开机自动运行；data 目录允许该身份修改，代码和密钥目录仅可读。日志：data/service.log。
- PBIRS P4Login.aspx 调用 `http://127.0.0.1:8765/internal/authenticate`；校验 HMACSHA256、30 秒时间窗和一次性 nonce；拒绝非回环来源。只返回稳定 principal，不返回密码及其哈希。Demo 不可用时登录失败关闭，不回退到旧账号文件。
- 原生登录表单保留 CSRF、重试限制、安全返回地址；Demo 已登录跳转仍采用一次性票据。账号库统一，浏览器会话独立；重置密码不自动撤销所有已有 PBIRS Cookie，停用通过撤销本演示资源 ACL 阻止既有会话访问。
- 防火墙开放 TCP8765，仅 LocalSubnet。测试 HTTP，适用于当前测试环境。
- 修改了登录页，不修改 DLL 或 FullTrust，rssrvpolicy/web/rsreportserver 配置哈希均与基线一致。登录页备份 `C:\ProgramData\P4DemoApp\backup-20261104-204142`。
- `deploy-shared/verify.py` 已在共享服务验证：admin 双入口登录、新建用户立即原生登录、A 授权/B 拒绝、改密立即生效、停用/恢复、已有原生会话权限撤销、外部访问内部认证接口拒绝。验收用户凭据位于 unified-review-login.local.json。


## 目录浏览与目录授权（2026-11-05）

共享 Demo 已部署目录版本，入口仍为 `http://pbirs.example.internal:8765/`。

- 我的报表按目录逐级浏览，支持面包屑和全局名称/路径搜索。目录结构来自 PBIRS 完整目录；每个返回的资源都用当前用户的 PBIRS 会话检查。只有单报表权限时，显示必要的虚拟祖先目录，不给祖先自动添加 Browser，避免继承造成同目录其他报表越权。
- 管理员可在授权树中选择文件夹（包括根目录）或单个报表。文件夹覆盖所有子目录与报表，界面显示来源目录。目录与单报表授权为并集：取消目录后，明确单独授权的报表继续保留。
- 账号库中的 accessSelection 保存明确的 folderIds/reportIds，PBIRS ACL 是实际访问执行层。旧用户原来的目录 Browser 是导航配置，迁移回显为实际报表授权，不将其误认为整个目录授权。
- 继承中的子资源随父目录原生继承；已有独立 ACL 的下级资源增加该用户的 Browser。需要给继承资源单独授权时，复制有效 ACL 再修改此用户，保留其他身份权限；不会重置其他人的 ACL。存在非 Browser 高级资源角色时拒绝覆盖，提示核查。
- 后台每 60 秒重新应用已管理用户的选择，覆盖新上传或移动到目录内的独立权限资源。新增资源可能有最多一个周期的授权延迟。停用清除所管理资源的查看授权，启用恢复原目录/报表选择。
- 备份：`C:\ProgramData\P4DemoApp\folder-backup-20261104-205251`。保留部署前代码与账号库快照；服务器活动账号库未被本地旧快照覆盖。PBIRS DLL、登录页及 FullTrust 配置本轮未修改，配置哈希仍与基线一致。
- 验证：`tests/test_folder_policies.py` 四项测试覆盖继承、单报表隔离、失败补偿与无效资源。`deploy-shared/verify_folders.py` 在共享服务实测目录授权覆盖独立 A/B、单报表不暴露其他报表、目录和直接授权叠加/撤销、临时嵌套目录、新独立报表自动授权、停用/恢复；逐项比较原有资源其他用户的角色保持不变。临时目录与报表已删除。
- 保留目录授权验收用户，凭据仅存 `folder-review-login.local.json`；授权 `/P4_Identity_Demo`。截图：`deploy-shared/folder-access.png`。


## 新增行级权限报表（2026-11-05）

独立目录 `/P6_RLS_Demo` 中已发布 `Province_RLS_Demo`，报表 ID `aa7993bf-c16e-426e-bf5c-1c2d2b32ccb9`。从共享 Demo 的“我的报表”进入该目录即可查看。

- demo1：Province_A，三行、金额 600。
- demo2：Province_B，三行、金额 1500。
- demo3：A+B，六行、金额 2100。
- admin/p4admin 可预览全部测试数据；普通用户查询仍用自己的身份。

模型使用六条合成测试数据，含金额、行数、当前身份卡片和明细表。原生 querydata 实测确认过滤和明细隔离，只有 Browser 未分配模型角色的身份被拒绝查询。原有用户其他报表授权保留。现已新增 Demo 行级权限管理页面，支持汇总读取全部报表角色、选择用户绑定并写回 PBIRS，见 rls-management/README.md。

制作、验证和源码见 `rls-demo/README.md`；结果见 `rls-demo/verification.json`；网页截图见 `rls-demo/demo1-iframe.png`。临时构建数据库与未完成草稿已清理，FullTrust 与原有配置哈希保持不变。


## 内嵌性能修复（2026-11-05）

已在服务器部署 gzip、静态私有缓存/ETag、HTTP1.1 与连接复用。修复前查看器每次传输约27MB，其中主脚本18.3MB，加载事件约73秒；压缩后主脚本约4.5MB，浏览器缓存命中后的重复打开实测约2.15秒。首次仍受网络下载速度影响，不能将热缓存结果视为冷启动承诺。

动态模型与数据查询继续 no-store，按当前用户请求，三个账号 RLS 回归通过。POST 正文统一读取以支持持续连接，匿名访问与退出登录回归通过。详见 perf-fix/README.md 和 perf-fix/verification.json。


第二轮优化已改为同源直接查看器，并将 Demo 连接发送缓冲区增至1MiB。专用浏览器仅清理静态缓存后，实际目录入口首次加载约19.5秒（主脚本真实网络下载约8.1秒），未使用热缓存充当首次结果。详细条件见 perf-fix/README.md。普通报表与 RLS 身份控制仍沿用原会话。
