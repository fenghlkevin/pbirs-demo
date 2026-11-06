# PBIRS 静态行级权限测试报表

报表入口：http://pbirs.example.internal/Reports/powerbi/P6_RLS_Demo/Province_RLS_Demo

Demo：http://pbirs.example.internal:8765/，在“我的报表”打开 P6_RLS_Demo 目录。

最终报表 ID：aa7993bf-c16e-426e-bf5c-1c2d2b32ccb9。

## 数据与权限

ProvinceSales 表使用 DATATABLE 生成六条合成测试数据，随 PBIX 内嵌保存，不依赖实际业务数据库或原报表的数据源。A 省 100/200/300，B 省 400/500/600。表内有省份、月份、记录编号、金额。

- Province_A：`[Province] = "A"`，demo1 的实际身份 p4:demo1。
- Province_B：`[Province] = "B"`，demo2 的实际身份 p4:demo2。
- demo3 同时属于 A、B，按两角色并集显示全部六行。
- Demo 管理员 p4:admin、原生门户管理员 p4:portaladmin 与维护身份 p4:maintenance 显式分配 A+B 便于管理和预览。业务查看不使用这些管理身份代替用户。

报表包含省份金额柱状图、VisibleAmount 金额卡、VisibleRows 行数卡、CurrentIdentity 身份卡，以及详细记录表。USERNAME() 使用自定义认证的实际用户标识。

## 制作过程与边界

在服务器独立的构建数据库 P4_RLS_Demo_Build 中，用 TOM/TMSL 建立已计算处理的模型并备份，封装到独立 PBIX。报表布局复用原演示报表的主题资源，图表绑定和模型均为新的测试内容。构建数据库完成后已经删除，报表数据保存在 PBIRS 自己加载的模型中。

模型角色必须包含稳定 PBI_Id 注解，PBIRS 的 DataModelRoles 才能识别 GUID。最终报表在首次上传时已含完整角色信息，并在分配用户后验证过滤。最初缺少完整角色元数据的草稿虽能渲染，但补充后未正确应用 RLS，该草稿及其资源授权均已清理，没有作为最终成果保留。后续开启或变更现有报表 RLS 仍需发布后做数据查询验收，不能只检查角色接口成功。

通过原生 REST DataModelRoleAssignments 配置了成员。后续已新增 Demo 的 RLS 管理 UI：从 PBIRS 读取现有模型角色，管理用户绑定并写回，见 ../rls-management/README.md。目录/报表查看授权仍独立管理。没有修改认证扩展、FullTrust、web.config 或 rsreportserver.config。

## 验证

`verify.py` 用三个各自的 PBIRS 会话查询同一原生 querydata 接口：

| 用户 | 省份 | 合计 | 明细行数 |
|---|---|---:|---:|
| demo1 | A | 600 | 3 |
| demo2 | B | 1500 | 3 |
| demo3 | A+B | 2100 | 6 |

同时验证：只有 Browser 报表权限、没有模型角色的测试身份无法查询数据（HTTP401/403），测试身份的临时资源授权已恢复删除。验证结果见 verification.json 和各账号 detail.json；不依赖 URL 或页面筛选器。

现有账户原来的报表选择保留，新测试报表作为额外授权加入。草稿已删除；单独的构建数据库已删除。重置密码或停用账号的现有会话限制仍沿用原 Demo 设计。
