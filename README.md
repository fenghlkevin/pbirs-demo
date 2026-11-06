# PBIRS Demo

基于系统账号的 Power BI Report Server 集成演示：统一账号登录、iframe 报表查看、用户管理、目录/报表授权，以及跨报表 RLS 角色分配。系统创建用户后，不需要同步创建 AD 域账号。普通用户的报表请求使用自己的 PBIRS 身份，维护身份仅用于受保护的授权管理接口。

本仓库收录 Demo 前后端、PBIRS C# 安全扩展和 ASPX 登录页、部署及排错脚本、测试、中葡双语资源、方案 PPT 与三语视频制作源码。原测试服务器的账号库、密码、签名密钥、原始权限快照、生成包、截图和视频未上传；内部地址已替换为示例地址。

## 目录

| 文件/目录 | 内容 |
|---|---|
| `server.py` / `index.html` | Demo 服务、管理界面、同源报表查看器代理 |
| `demo_admin.py` / `rls_admin.py` | 账号、资源策略、模型角色分配和回读 |
| `ticket_auth.py` | 短时一次性身份票据和 PBIRS Forms 会话 |
| `custom-security/` | PBIRS 认证/授权扩展、自定义登录页及部署源码 |
| `deploy-shared/` | 同服务器部署与集成验收 |
| `bilingual/` | 中文、安哥拉葡萄牙语文案及部署脚本 |
| `rls-demo/` | 六条合成数据的 RLS 模型和报表制作脚本 |
| `rls-management/` | 跨报表 RLS 角色管理及验收 |
| `admin-fix/` / `portal-deploy/` / `portal-nav-fix/` / `perf-fix/` | 门户兼容、导航、部署、性能修复记录 |
| `tests/` | 可离线执行的策略、RLS 和 HTTP 测试 |
| `presentations/` / `presentation-update/` | 方案演示文稿制作源码 |
| `video-zh/` / `video-multilang/` | 中文、葡语、英语视频脚本和制作程序 |

## 初始化与运行

需要 Python 3.10+。PBIRS 扩展构建和安装在 Windows/PBIRS 主机进行；本仓库不是一键安装包。

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python init_demo.py
export P4_PBIRS_URL='http://your-pbirs-host'
export P4_PUBLIC_URL='http://127.0.0.1:8765'
export P4_BIND='127.0.0.1'
.venv/bin/python server.py
```

`init_demo.py` 生成全新的随机密钥及 demo1/demo2/demo3/admin/p4admin 账号，密码只写入权限为 0600 的 `*.local.json`，不会打印或提交。它不连接 PBIRS，不创建域账号，也不授予报表权限。已有本地配置时拒绝覆盖。

启动前还需在目标 PBIRS 安装对应安全扩展和登录页、配置 Forms 认证、部署相同的票据密钥，并建立维护/管理员资源策略。参考 `custom-security/`、`deploy-shared/` 与 [开发部署记录](docs/DEVELOPMENT_NOTES.md)。记录按实际开发阶段保留，部分脚本属于历史迁移或诊断步骤，不应全部顺序执行。Windows 安装目录及示例主机地址需要按目标环境调整；集成验收脚本需要本地凭据和目标环境已有报表 ID。

本次公开整理只让主服务及票据模块通过 `P4_PBIRS_URL` 配置上游地址；历史脚本中的 `pbirs.example.internal` 是占位符。`.env.example` 用于说明变量，程序不会自动加载 `.env`。

## 测试

初始化本地配置后执行：

```sh
.venv/bin/python -m unittest discover -s tests -v
```

`verify_*.py` 和各目录的 `verify.py` 为真实服务器集成验收，可能新建临时资源、修改测试用户授权，需准备隔离环境及各脚本引用的本地凭据。它们不属于离线单元测试。

## 权限设计

- 用户标识采用稳定的 `p4:*` subject，PBIRS 不保存第二份业务用户密码。
- Demo 管理员通过接口更新 PBIRS Browser 资源策略；目录授权覆盖子资源，明确的单报表授权与目录授权取并集。
- RLS 规则在 Desktop/模型中定义并发布。Demo 读取既有模型角色，把用户成员关系写回 PBIRS，不在前端模拟安全过滤。
- 跨报表保存会保留其他用户成员分配，进行版本检查和回读，并逐项报告失败；不宣称跨报表事务。
- 业务角色自动展开为用户属于后续设计，尚未实现。
- 保留原生报表引擎和门户。当前方案未修改 FullTrust 配置；仓库中的签名/信任提案脚本不代表已启用。

## 辅助制作源码

部署/维护及视频脚本还需 `requirements-dev.txt` 中的依赖。PPT 程序依赖原制作环境的演示文稿工具；截图、基础 PBIX、模型备份、语音和渲染产物未提交，重建前需按脚本说明自行提供。视频脚本保留了原制作平台的 macOS 字体路径，其他平台需替换。英文界面为录制预览，当前部署版 Demo 为中葡双语。

这是一套测试验证程序。正式接入需补齐 HTTPS、密钥托管、共享 nonce/会话撤销、审计和权限同步机制。更详细的已验证能力及限制见各目录 README 和开发部署记录。
