# 内嵌报表加载优化

已部署在共享 Demo，服务器备份：C:\ProgramData\P4DemoApp\perf-backup-20261104-231342。

## 原因与修改

此前 Demo 代理对所有响应统一 no-store，没有向浏览器压缩脚本/HTML，并使用 HTTP/1.0。PBIRS 查看器每次都重复传输大量组件。本次修改只在 Demo 的 server.py：

- HTTP/1.1 持续连接、TCP_NODELAY、监听队列128，复用现有按用户的上游会话连接。
- 支持 gzip（level6），压缩文本、HTML、脚本、JSON；已压缩图片、字体等不重复压缩。
- 仅明确静态目录 /Reports/assets/、/powerbi/libs/、/powerbi/assets/ 返回 private,max-age=3600、Vary、ETag，支持304；服务端保存静态原文和压缩副本。
- 动态页面、模型和 querydata 仍为 no-store。未缓存用户数据，不按管理员身份查看。每个代理请求仍先校验有效 Demo 用户，再调用该用户的 PBIRS 会话。
- 新增 Server-Timing 上游耗时，区分 PBIRS 请求时间和浏览器传输。
- HTTP/1.1 下统一预读并保存请求体，避免 /api/logout 等提前返回的 POST 将未读正文污染后续请求。

## 实测结果

同一测试浏览器、相同报表 Province_RLS_Demo，用户 demo1。浏览器 navigation.loadEventEnd 记录查看器加载事件，另通过 DOM 确认图表、金额600、三行及 p4:demo1 正常渲染。不是跨网络条件的性能承诺。

| 项目 | 修复前 | 修复后 |
|---|---:|---:|
| 查看器资源传输量 | 约27.0MB | 首次gzip测试约7.6MB，重复约13KB（不含导航正文） |
| 最大主脚本传输 | 18,341,044 字节 | 4,488,319 字节（level6） |
| 最大主脚本下载 | 约67.7秒 | 独立HTTP请求约16.3秒，缓存命中0毫秒/0网络字节 |
| 查看器 load 事件 | 约73.3秒 | 首次gzip level3测试约33.1秒，最终版本重复打开约2.15秒 |

首次仍需下载核心组件，耗时受当前网络带宽影响。已缓存公共组件可以跨不同报表复用，第一次遇到的新可视化组件仍需下载。不要将缓存后的结果作为全新浏览器冷启动结果。

## 验证

- tests/test_http_transport.py：三项通过，覆盖 POST 提前返回后的持续连接、正文读取、gzip、304、动态 no-store、禁止压缩时的原文。
- perf-fix/verify.py：共享服务实测三账号代理 RLS 仍分别返回 A600/B1500/A+B；静态 gzip/私有缓存/ETag、HTTP1.1、匿名拒绝、退出后拒绝通过。
- 未修改 PBIRS 的 DLL、认证配置、FullTrust、资源策略或模型角色。三项配置哈希仍与先前基线一致。


## 第二轮首次加载优化

部署备份：`C:\ProgramData\P4DemoApp\firstload-backup-20261104-232345`。

- PowerBIReport 的 iframe 改为同源代理 `/powerbi/?id=<报表ID>&formatLocale=zh-CN`，直接加载查看器，省去 `/Reports/powerbi/...` 外层门户和第二层 iframe。仍通过 Demo 后端携带当前用户的 PBIRS Cookie 请求，不改用管理员会话。分页报表入口保持原来方式。
- 仅 Demo 进程的连接设置 SO_SNDBUF=1MiB（此前 Windows 默认131072字节），改善较高延迟连接的大资源发送。不修改操作系统 TCP 全局设置。
- 采用当前服务器实际提供的查看器 URL，属于与 PBIRS 版本关联的接入点，升级需回归；需要时可恢复官方门户包装入口。

在专用 pbirs-demo 浏览器设置中，仅清理过去24小时“缓存的图片和文件”，明确保留 Cookie、浏览记录与下载记录。重新登录 demo1，通过 Demo 正常目录/查看报表按钮打开，主脚本实际网络传输4,488,619字节（含浏览器统计头部），排除缓存命中。

实测首次查看器 loadEventEnd=19,539ms，主脚本下载8,096ms、PBIRS上游682.4ms，查看器资源网络传输合计6,677,788字节（不含导航HTML）。随后DOM确认金额600、三行、p4:demo1。测试期间还并发运行了后端回归脚本，因此不是空闲网络实验，也不是上线SLA。

第二轮 HTTP 三项测试与代理 RLS/缓存/退出回归均通过，三个账号仍返回A600/B1500/A+B2100。首次约20秒是当前网络实测值，缓存后的约2秒属于前一轮测量；首次剩余主要耗时来自核心查看器资源传输，不能承诺零等待。
