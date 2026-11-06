# Windows 本地账号版本（featrue-1.0.1）

本分支新增 `ad_server.py` 和 `ad/index.html`。当前采用 Windows 本地账号；AD 只读连接代码保留为可选来源，不要求测试服务器加入域。旧 Forms 入口 `server.py` 仅保留供历史回滚，不作为本版本入口。

## 身份与权限

浏览器通过 `windows-gateway.ps1` 的 HTTP.sys Windows 认证入口登录。网关仅信任 Windows 实际验证的用户名，以 HMAC 对方法、原始路径、正文摘要、用户、时间和一次性 nonce 签名，转发至 127.0.0.1 后端。后端拒绝未签名、篡改及重放请求，POST 还检查 Origin。普通用户不能调用管理接口。

报表 iframe 直接访问 PBIRS，使用浏览器自己的 Windows 身份；不经过管理员查看代理。首次访问不同地址/端口，浏览器可能再次提示 Windows 凭据；这不等同于已实现跨站无感 SSO。不能用 Demo 菜单过滤代替 PBIRS 授权。

后端以 Windows 任务运行账号的 SSPI 身份调用 PBIRS 管理 API。测试部署明确授权使用 Administrator；正式环境应改用有明确资源管理范围的专用账号。

本地账号由 `Get-LocalUser` 读取，SID 作为稳定 ID，读取启用状态和本地组。提供页面手动拉取及默认 300 秒自动同步，不创建用户、不重置密码、不写回 Windows。保留已有授权选择，失踪账号标为不在范围；账号更名会拒绝覆盖，先迁移 PBIRS 原身份授权。同步范围移除本身不保证撤销 PBIRS 直接访问或现存会话。

目录/报表绑定使用 PBIRS 原生 Browser 策略。模型角色绑定使用 DataModelRoleAssignments，保留其他用户及组。Windows 身份比较不区分大小写。页面单独显示组来源；取消个人绑定不会消除组授权。多个 RLS 角色通常按可见范围并集执行。

## 配置与启动

安装 `requirements-ad.txt`，按 `local.env.example` 设置环境变量（程序不自动加载 dotenv）。服务数据目录应只允许任务运行账号与 SYSTEM/Administrators 访问，尤其是网关签名密钥和目录快照。

1. PBIRS 恢复原生 Windows 认证和原生 Windows 授权扩展，确认有效维护账号可访问根目录。
2. 运行 `python ad_server.py`，首次完整账号同步成功后才打开后端监听。
3. 配好 HTTP.sys URL ACL/HTTPS 证书，使用同一组环境变量启动 `windows-gateway.ps1`。
4. 浏览器通过 P6_PUBLIC_URL 打开 Demo。不要对外开放后端端口。

本测试沿用内网 HTTP；对外使用需配置 HTTPS。网关当前串行处理请求，适用于本次 Demo，不是生产并发网关。

## RLS 规则只读展示

配置 `P6_RULES_PATH`、`P6_TOM_LIBRARY`（含 Microsoft.AnalysisServices.Core.dll / Tabular.dll 的目录）及 `P6_ENGINE_PORT_FILE`（PBIRS 嵌入模型的 msmdsrv.port.txt）。管理员读取用户 RLS 时，后台调用 `export-rules.ps1`，从原生 API 获取模型 runtime ID，用 TOM 只读读取角色 PBI_Id、表名与 FilterExpression。忽略引擎内部 RSReaderRole，不修改模型。

可选 `P6_MODEL_BINDINGS_PATH` 用于固定模型映射，结构见 `model-bindings.example.json`。运行模型端口及此读取方式依赖 PBIRS 版本，升级必须回归；它不是对外公开的规则 REST API。

快照绑定报表 ModifiedDate、模型角色 ID 与名称，默认最多 600 秒有效。报表重新发布、角色变化、模型不可访问或采集失败会显示“规则未采集、读取失败或已过期”，不会把失败显示为“没有规则”。Analysis Services live connection 的源端规则不在本实现覆盖内。

## 从旧 Forms Demo 恢复时的注意事项

恢复原 Windows 配置不会自动转换只在 Custom 下创建的安全描述符。部分旧目录在 Windows 下会报授权扩展错误。不要把所有资源统一授予 Administrators 来绕过；保留原有 Windows 策略和迁移前备份。在独立原生 Windows 目录发布演示报表后配置本地账号。页面将不可读旧策略明确标记且禁止覆盖；这些旧资源仍需独立迁移，不宣称已全部兼容。

离线验证：`python -m unittest discover -s tests -v`。真实验收还需 Windows 服务器、用户凭据及已配置的原生 PBIRS。旧 Forms 集成脚本不可用于 Windows 分支验收。
