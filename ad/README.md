# Demo 独立登录 + PBIRS Windows 认证

入口为 `ad_server.py` 与 `ad/index.html`。Windows/AD 账号资料同步到 Demo，Demo 保存独立密码哈希并验证登录。PBIRS 保持原生 Windows 认证；管理员为每个用户单独配置 Windows 报表凭据，后端以该用户的 NTLM 身份代理报表，不代用管理账号。

## 账号与登录

- Windows 本地账号通过 `Get-LocalUser` 同步，以 SID 作为稳定 ID；可选 AD 来源使用 LDAPS，以 objectGUID 作为稳定 ID。
- 手动或默认 300 秒定时同步用户资料、启用状态和组，保留 Demo 密码、Windows 加密凭据与报表绑定。同步不创建或改密 Windows 账号。
- 登录调用 Demo `/api/login`，使用 PBKDF2-SHA256 验证 Demo 密码，签发 HttpOnly/SameSite 会话 Cookie。退出、Demo 改密和源账号停用使 Demo 会话失效。
- Windows 密码不能通过账号同步取得。管理员在“账号同步”分别设置 Demo 密码及 Windows 报表凭据。配置报表凭据时先调用 PBIRS `/me` 验证用户名一致，再使用当前 Windows 服务用户的 DPAPI 加密保存。
- 没有 Windows 凭据的用户仍可登录 Demo；报表入口提示需要管理员配置，不使用管理员兜底。不向浏览器返回密码、哈希或密文。
- 登录页不再使用浏览器的 Windows 身份，也不弹 Windows 登录框。直接访问 PBIRS 原生门户仍按其 Windows 认证处理。

数据目录只允许任务账号和 SYSTEM/Administrators 访问。DPAPI 绑定服务用户；迁移服务账号或主机前应重新配置凭据。当前内网测试使用 HTTP，生产应配置 HTTPS。

## 部署

安装 `requirements-ad.txt`（包含 Windows 上的 pywin32 依赖），按 `local.env.example` 设置环境变量；程序不会自动加载 dotenv。后端监听 loopback，HTTP.sys 网关运行 `windows-gateway.ps1`，以 Anonymous 接收浏览器请求，仅转发到后端，由 Demo 会话认证保护 API 和报表代理。不要对外开放后端端口。

管理 API 使用任务运行账号的 SSPI，仅用于元数据和授权。测试环境已授权使用 Administrator 运行现有任务；报表浏览单独使用当前 Demo 用户已配置的 Windows 凭据。正式环境应改用授权范围明确的服务账号。

已有 Demo 的密码哈希可通过一次性导入配置迁移：`P6_DEMO_IMPORT_PATH` 指向旧账号 JSON，`P6_DEMO_IMPORT_MAP` 为旧 Demo 账号到 Windows 短账号名的 JSON 映射。仅填补未设置的 Demo 密码，不覆盖已有密码，不导入或猜测 Windows 密码。新用户先由管理员设置 Demo 密码。

## 报表授权与 RLS

授权树显示实际目录层级，支持展开/折叠。目录选择覆盖下级，单独选择保留；树中标记来自上级的授权。保存调用 PBIRS 原生资源策略，保留其他用户和组。

RLS 以有模型角色的报表为主展示，显示表名与 DAX，单独收起无角色与读取失败的报表。加载、修改、保存和部分失败都有状态反馈，保存结果逐项回读；已成功项更新版本，失败项保留草稿。Windows 组授权单独展示，取消直接绑定不等于取消组授权。

配置 `P6_RULES_PATH`、`P6_TOM_LIBRARY` 和 `P6_ENGINE_PORT_FILE`，后台从 REST 获取运行模型 ID，用 TOM 只读采集角色 PBI_Id、表名和 FilterExpression。忽略内部 RSReaderRole。规则快照验证报表 ModifiedDate、角色 ID/名称及有效期；失败不伪装成没有规则。固定模型映射可配置 `P6_MODEL_BINDINGS_PATH`。此读取方式依赖 PBIRS 内部模型运行机制，升级需回归；Analysis Services live connection 的源端规则不在本实现覆盖内。

旧 Custom-only 资源可能没有可用的 Windows 安全描述符。保留原 Windows 策略，旧资源读取失败时禁止覆盖，不能给所有资源统一增加管理员权限。本地账号演示使用独立原生目录；未迁移旧资源会在错误明细中显示。

## 验证

`python -m unittest discover -s tests -v`

`node tests/test_resource_tree.cjs`

真实验收应使用“独立 Demo 密码 + 不同的 Windows 密码”验证登录、会话隔离、目录树授权、用户自身 querydata 的 A/B/并集 RLS，以及撤权和退出后的拒绝访问。
