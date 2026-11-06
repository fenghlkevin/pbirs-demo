const C={navy:'#082E5C',blue:'#1466A8',ink:'#17304C',muted:'#576F88',pale:'#EFF5FB',gold:'#DDA435',green:'#26744B',line:'#CAD8E6',white:'#FFFFFF'};
const FONT='Microsoft YaHei';
const ROOT='/path/to/pbirs-demo';
const SRC={intro:'https://learn.microsoft.com/en-us/power-bi/report-server/developer-handbook-overview',compare:'https://learn.microsoft.com/en-us/power-bi/report-server/compare-report-server-service',auth:'https://learn.microsoft.com/en-us/sql/reporting-services/extensions/security-extension/authentication-in-reporting-services',acl:'https://learn.microsoft.com/en-us/sql/reporting-services/security/role-assignments',rls:'https://learn.microsoft.com/en-us/power-bi/report-server/row-level-security-report-server',rest:'https://learn.microsoft.com/en-us/power-bi/report-server/rest-api',roles:'https://learn.microsoft.com/en-us/rest/api/power-bi-report/power-bi-reports/get-power-bi-report-data-model-roles',assign:'https://learn.microsoft.com/en-us/rest/api/power-bi-report/power-bi-reports/replace-power-bi-report-data-model-role-assignments'};
function text(s,value,x,y,w,h,size=24,color=C.ink,bold=false){const t=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});t.text=value;t.text.style={fontFamily:FONT,fontSize:size,color,bold};return t}
function slide(p,title,sub,notes=''){const s=p.slides.add({width:1280,height:720});s.background.fill=C.white;text(s,title,64,44,1150,65,36,C.navy,true);if(sub)text(s,sub,66,118,1140,52,21,C.muted);text(s,String(p.slides.items.length).padStart(2,'0'),1170,666,50,28,16,C.muted);s.speakerNotes.text=notes;return s}
function node(s,label,x,y,w=240,h=100,fill=C.pale,color=C.ink){const n=s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill,line:{fill:C.line,width:1}});n.text=label;n.text.style={fontFamily:FONT,fontSize:24,color,alignment:'center',verticalAlignment:'middle',bold:true};return n}
function arrow(s,a,b,from='right',to='left',color=C.blue){return s.shapes.connect(a,b,{kind:'straight',fromSide:from,toSide:to,line:{fill:color,width:2.5},tail:{type:'triangle',width:'med',length:'med'}})}
function table(s,values,x,y,w,h,widths,size=21){const tb=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,columnWidths:widths,values});tb.borders.assign({fill:C.line,width:1,style:'solid'});for(let r=0;r<values.length;r++)for(let c=0;c<values[r].length;c++){const cell=tb.getCell(r,c);cell.fill=r===0?C.navy:(r%2?C.white:C.pale);cell.text.style={fontFamily:FONT,fontSize:size,color:r===0?C.white:C.ink,bold:r===0};}return tb}
function img(s,name,x,y,w,h,alt,crop){return s.images.add({path:ROOT+'/'+name,alt,position:{left:x,top:y,width:w,height:h},fit:'contain',...(crop?{crop}:{})})}
export async function build({presentation:p,input}){
const batch=input.batch;
if(batch===1){
 {let s=slide(p,'PBIRS 是企业内部的报表服务器','PBIRS = Power BI Report Server，负责存放、展示和保护报表',`产品定义与 iframe 能力：${SRC.intro}\nDemo 实现依据：README.md、server.py。`);
 const a=node(s,'报表作者\nPower BI Desktop',64,240,255,120),b=node(s,'PBIRS\n报表与数据模型',502,240,265,120,C.navy,C.white),c=node(s,'业务用户\nP6 页面或门户',947,240,265,120);arrow(s,a,b);arrow(s,b,c);
 text(s,'制作并发布报表',94,382,235,45,23,C.blue);text(s,'执行查询与权限检查',493,382,300,45,23,C.blue);text(s,'浏览与交互分析',962,382,250,45,23,C.blue);
 text(s,'P6 管理业务入口和用户，PBIRS 提供报表展示能力',78,504,1110,62,29,C.navy,true);
 text(s,'报表文件常见为 .pbix，分页报表使用 .rdl。PBIRS 可以部署在企业自己的服务器。',78,590,1110,58,21,C.muted);}
 {let s=slide(p,'Report、业务看板与云端 Dashboard','业务界面叫“看板”，并不意味着 PBIRS 中存在一个 Dashboard 对象',`产品能力对比：${SRC.compare}\n右侧为测试服务器原生 Report_A 截图，p4admin-report-fixed.png。截图只证明报表展示，不代表业务大屏已经迁移。`);
 text(s,'Report：交互式报表',65,206,510,46,28,C.blue,true);text(s,'可包含多页、图表和筛选器\nPBIRS 中对应 PowerBIReport 资源',65,270,470,95,25);
 text(s,'业务看板：页面呈现方式',65,396,500,46,28,C.blue,true);text(s,'可以是一页 Power BI 报表\n也可以由 P6 组织多个报表入口',65,458,470,100,25);
 img(s,'p4admin-report-fixed.png',575,200,645,365,'测试环境中的 Power BI 交互式报表');text(s,'PBIRS 没有云版 Power BI 的原生 Dashboard 对象',65,606,1130,48,24,C.navy,true);}
 {let s=slide(p,'PBIRS 身份集成的两条主路线','选型取决于用户由谁管理，以及企业是否统一使用 Windows 域账号',`Windows / 自定义认证机制：${SRC.auth}\n本项目经历过 AD 账号映射测试，最终选择自定义认证。Power BI Service 与 PBIRS 是不同产品：${SRC.compare}`);
 table(s,[['路线','用户身份来源','免登录的前提','对本项目的影响'],['Windows 集成认证','AD 域账号','浏览器与域环境配合\nNTLM / Kerberos','需关联 P6 用户与域身份'],['自定义认证（本次选择）','P6 现有账号体系','认证接口与身份票据\nPBIRS 安全扩展','新建用户无需创建 AD 账号']],64,205,1150,262,[240,245,335,330],22);
 text(s,'选择原因',65,499,220,45,27,C.blue,true);text(s,'P6 已有用户管理，账号生命周期应由 P6 统一负责。',255,505,930,42,26);
 text(s,'AD 用户密码代理只是前期验证方式。云版 Power BI Embedded 属于另一产品路线。',65,578,1140,60,21,C.muted);}
 {let s=slide(p,'方案架构与系统分工','账号统一在业务系统，报表与访问执行仍在 PBIRS',`Demo 当前部署同服务器。正式 P6 需要替换 Demo 认证与账号服务，尚未连接正式 Keycloak/IAM。实现依据：server.py、ticket_auth.py、demo_admin.py、custom-security/P4Login.aspx、custom-security/P4Security.cs。自定义认证机制：${SRC.auth}`);
 const a=node(s,'P6 / 当前 Demo\n账号、用户状态、授权界面',65,225,345,140),b=node(s,'集成服务\n认证接口、票据、权限 API',468,225,345,140),c=node(s,'PBIRS\n安全扩展、报表、资源策略',870,225,345,140,C.navy,C.white);arrow(s,a,b);arrow(s,b,c);
 text(s,'唯一账号来源',80,412,330,42,27,C.blue,true);text(s,'验证身份并办理授权',480,412,345,42,27,C.blue,true);text(s,'按当前用户检查访问',878,412,345,42,27,C.blue,true);
 text(s,'用户标识示例：p4:u_xxx',80,474,1080,42,25);text(s,'稳定标识连接账号与权限。PBIRS 不保存第二份用户密码，也不需要给业务用户创建 AD 账号。',80,530,1100,84,25);
}
}
if(batch===2){
 {let s=slide(p,'从 P6 打开报表的免重复登录流程','单点登录表示只认证一次，P6 与 PBIRS 仍分别持有自己的会话',`实现依据：ticket_auth.py issue_ticket / establish，server.py /api/login、/api/browser-ticket 与代理路由。Demo 的 iframe 由后端携带当前用户的 PBIRS Cookie 转发。点击“打开 PBIRS 门户”则通过浏览器 POST 一次性票据建立浏览器会话。票据是项目自定义 HMAC 票据，不是云版 Embed Token。`);
 const a=node(s,'1  登录 P6\n校验现有账号',64,220,250,110),b=node(s,'2  签发身份票据\n绑定当前用户',455,220,300,110),c=node(s,'3  PBIRS 验票\n建立该用户会话',930,220,285,110,C.navy,C.white);arrow(s,a,b);arrow(s,b,c);
 const d=node(s,'4  报表请求\n带该用户 PBIRS 会话',455,430,300,110),e=node(s,'5  权限检查与渲染\n返回允许访问的内容',930,430,285,110,C.navy,C.white);arrow(s,c,e,'bottom','top');arrow(s,d,e);
 text(s,'后续请求复用会话',73,446,320,74,25,C.blue,true);text(s,'票据只用于建立身份：短时有效、签名校验、一次性消费。',68,601,1120,52,24,C.muted);}
 {let s=slide(p,'直接进入 PBIRS 也使用同一套账号','当前实现保留 PBIRS 登录页，由服务端调用 Demo 认证接口',`真实现状：不是浏览器重定向到 Demo 首页。PBIRS /ReportServer/P4Login.aspx 表单收到用户名密码后，向 http://127.0.0.1:8765/internal/authenticate 发签名请求；Demo 校验密码哈希与 enabled，返回 principal。PBIRS 通过票据消费设置 Forms Cookie。认证失败关闭，不回退旧账号文件。实现依据：P4Login.aspx Verify，server.py internal_authenticate。`);
 const a=node(s,'浏览器\n访问 PBIRS',65,228,215,112),b=node(s,'PBIRS 登录页\n采集系统账号',365,228,245,112),c=node(s,'Demo 认证接口\n校验账号与状态',755,228,280,112,C.navy,C.white);arrow(s,a,b);arrow(s,b,c);text(s,'服务端调用',620,241,135,44,20,C.blue);
 const d=node(s,'PBIRS 会话\n使用返回的用户标识',755,442,280,110,C.navy,C.white);arrow(s,c,d,'bottom','top');text(s,'新增账号、修改密码和停用\n都只在 Demo 账号库维护',65,449,610,105,30,C.blue,true);
 text(s,'正式接入时，将 Demo 的验证逻辑替换为 P6 现有认证服务。',65,606,1130,45,24,C.muted);}
 {let s=slide(p,'iframe 内嵌后的页面效果','P6 提供导航与业务页面，iframe 内仍由 PBIRS 渲染交互式报表',`截图：demo-p4-ticket-report.png，前期已验证的本人身份票据内嵌效果。截图界面沿用 P4/Demo 名称。iframe 参数由官方开发指南支持：${SRC.intro}\nDemo 实际采用同源代理：浏览器请求 Demo 路径，Demo 使用当前用户 PBIRS Cookie 转发。此处未采用云版 Power BI JavaScript SDK 或 Embed Token。正式域名部署仍需验证 HTTPS、Cookie、CSP/frame-ancestors 与跨域设置。`);
 img(s,'demo-p4-ticket-report.png',64,184,855,430,'实际 Demo 中内嵌 Power BI 报表的效果');
 text(s,'外层：业务平台',962,214,252,45,28,C.blue,true);text(s,'目录、搜索、用户与权限入口',962,272,250,95,24);
 text(s,'内层：PBIRS 报表',962,398,252,45,28,C.blue,true);text(s,'图表、筛选和数据交互',962,456,250,90,24);
 text(s,'?rs:embed=true 控制展示形式。免重复登录来自前面的身份会话。',65,622,1140,50,23,C.navy,true);}
 {let s=slide(p,'报表安全包含资源权限与行级权限','先决定能否打开报表，再决定报表内能看到哪些数据',`资源角色：${SRC.acl}\nRLS 定义与限制：${SRC.rls}\n当前 Demo 已实现资源级权限，RLS 仅为后续设计，尚未开发和实测。`);
 const a=node(s,'当前用户',65,265,220,110),b=node(s,'资源权限\n允许查看这张报表？',397,265,330,110),c=node(s,'行级权限 RLS\n允许查看哪些数据？',853,265,360,110,C.navy,C.white);arrow(s,a,b);arrow(s,b,c);
 text(s,'例：可以打开《缴费分析》',397,405,390,85,26,C.blue,true);text(s,'例：只看到自己负责的省份',853,405,360,85,26,C.blue,true);
 text(s,'已验证：目录与报表授权',65,551,540,60,29,C.green,true);text(s,'待验证：模型角色与数据行过滤',650,551,565,60,29,C.muted,true);
}
}
if(batch===3){
 {let s=slide(p,'目录授权与单报表授权','用户最终权限是目录覆盖范围与单独报表授权的并集',`Demo 依据：demo_admin.py replace_selection、selection_for、reconcile_permissions，index.html renderAccess。原生角色继承见 ${SRC.acl}。本 Demo 对独立 ACL 的后代增加本人 Browser，不重置其他用户权限。新增资源由 60 秒轮询补齐。`);
 const a=node(s,'张三\n授权财务目录',65,225,230,110),b=node(s,'/财务',450,225,220,100,C.navy,C.white),c=node(s,'月报 A\n可查看',890,182,250,90),d=node(s,'月报 B\n可查看',890,332,250,90);arrow(s,a,b);arrow(s,b,c);arrow(s,b,d);
 text(s,'目录覆盖全部下级资源',65,445,610,50,29,C.blue,true);text(s,'已有独立权限的报表也会匹配授权\n新增资源最多一个轮询周期后生效',65,512,650,105,25);
 text(s,'若只单独授权 A\nB 仍然无权访问',847,499,340,95,27,C.navy,true);}
 {let s=slide(p,'管理员在自己的平台中完成授权','后台将选择写入 PBIRS 真实资源策略，前端列表只是展示结果',`左图为 deploy-shared/folder-access.png 的目录与下级报表区域，使用图片裁切展示。当前 Demo 管理员 admin、原生门户管理身份 p4:portaladmin、后台授权维护身份 p4:maintenance 是不同职责。维护身份只办理控制面操作，不用于替用户查看报表。实现依据：demo_admin.py、server.py、P4Security.cs。`);
 img(s,'deploy-shared/folder-access.png',63,208,690,330,'真实目录授权界面中勾选目录后覆盖 Report_A 与 Report_B',{left:0.315,top:0.56,right:0.145,bottom:0.27});
 text(s,'管理员选择用户与资源',815,210,390,60,29,C.blue,true);text(s,'集成服务写入 Browser 查看角色\nPBIRS 对直链和内嵌同样检查权限',815,289,390,128,25);
 text(s,'管理身份与查看身份分开',815,463,390,52,27,C.navy,true);text(s,'维护身份只执行授权操作\n普通访问始终使用当前用户',815,527,390,95,24);
 text(s,'单报表授权不会自动扩大为整个目录的查看权限',65,605,680,52,24,C.navy,true);}
 {let s=slide(p,'行级权限的后续接入方式','RLS = Row-Level Security，在同一张报表中按用户过滤数据',`后续方案，尚未实现。官方依据：${SRC.rls}\n自定义认证下 USERNAME()/USERPRINCIPALNAME() 返回自定义用户名。自定义认证不能依赖 Windows 组完成 RLS 成员关系，需要显式用户成员分配。可用 GET DataModelRoles 与 PUT DataModelRoleAssignments，见 ${SRC.roles} 和 ${SRC.assign}。Import 与使用存储凭据的 DirectQuery 可采用 PBIRS RLS；Analysis Services live connection 的 RLS 在数据源模型处理，DirectQuery integrated-security 不使用此路径。`);
 const a=node(s,'P6 业务授权\n张三负责省份 A',65,224,300,110),b=node(s,'同一用户标识\np4:u_xxx',470,224,290,110),c=node(s,'报表模型中的 RLS\n区域查看角色',865,224,350,110,C.navy,C.white);arrow(s,a,b);arrow(s,b,c);
 text(s,'报表作者',65,407,245,42,27,C.blue,true);text(s,'在 Desktop 定义角色与过滤规则，再发布报表',310,411,875,45,25);
 text(s,'集成服务',65,488,245,42,27,C.blue,true);text(s,'将用户标识关联到模型角色，维护用户与省份关系',310,492,875,72,25);
 text(s,'PBIRS / 数据模型',65,580,245,50,26,C.blue,true);text(s,'查询时按当前身份执行过滤，前端筛选参数不承担安全控制',310,584,875,70,24);}
 {let s=slide(p,'同一报表，不同用户看到不同数据','下面是行级权限设计示意，尚未在当前 Demo 实测',`设计示意数据，不是实际业务统计。根据官方 RLS 文档 ${SRC.rls} 设计。资源 Browser 角色与模型 RLS 角色是不同层级，不能直接等同。自定义认证需要显式用户角色成员分配。`);
 table(s,[['用户身份','P6 业务范围','PBIRS 模型角色','报表可见数据'],['张三：p4:u_A','省份 A','RegionViewer','仅省份 A 的记录'],['李四：p4:u_B','省份 B','RegionViewer','仅省份 B 的记录']],65,225,1145,245,[285,230,275,355],24);
 text(s,'同一个模型角色可以配合用户与区域关系表实现动态过滤',65,526,1140,54,28,C.blue,true);
 text(s,'业务角色、资源 Browser 角色和模型 RLS 角色分别管理，通过稳定用户标识建立关联。',65,602,1135,65,23,C.muted);
}
}
if(batch===4){
 {let s=slide(p,'PBIRS 可以提供的元数据','P6 通过接口读取目录与权限信息，不需要复制报表数据才能建目录',`官方 REST API 概述：${SRC.rest}\n模型角色接口：${SRC.roles}\n已验证接口：GET /CatalogItems、GET /Folders(id)/Policies、GET /PowerBIReports(id)/Policies。当前目录返回并展示 Id/Name/Path/Type。其他创建修改时间等目录属性以服务器版本返回值为准。当前模型角色与角色分配 API 仅调研未联调，不宣称可读取完整 DAX 过滤表达式。PBIRS 不存在原生云端 Dashboard 对象。`);
 table(s,[['元数据','P6 中的用途','当前状态'],['文件夹与报表：ID、名称、路径、类型','构建目录树、检索与打开报表','已验证'],['资源策略：用户标识、角色、继承关系','回显授权并核对实际访问','已验证'],['模型角色与用户成员分配','维护 RLS 角色映射','官方 API 可用，待联调'],['数据源、刷新计划、订阅等','后续资产管理与运维','按需扩展，受版本和权限限制']],65,202,1145,350,[500,405,240],22);
 text(s,'业务角色、部门和业务标签由 P6 管理。PBIRS 角色不会自动变成 P6 的业务角色。',65,593,1140,65,24,C.navy,true);}
 {let s=slide(p,'账号、授权与资产信息的管理方向','分别明确主数据来源，避免两个系统互相覆盖',`当前依据：账号库在 Demo，PBIRS 登录实时调用认证接口，不同步账号密码副本。accessSelection 保存明确授权，replace_selection 写入资源策略，后台每60秒核对。CatalogItems读取资产元数据，用户列表按本人会话核权。P6 正式资产缓存、审计、同步任务尚未实现。`);
 const a=node(s,'P6\n账号与用户状态',65,210,325,110),b=node(s,'PBIRS\n认证与用户会话',865,210,350,110,C.navy,C.white);arrow(s,a,b);text(s,'实时认证接口 / 身份票据',433,230,400,53,25,C.blue);
 const c=node(s,'P6\n目录与报表授权选择',65,386,325,110),d=node(s,'PBIRS\n资源角色策略',865,386,350,110,C.navy,C.white);arrow(s,c,d);text(s,'授权接口写入与定期核对',433,407,400,53,25,C.blue);
 const e=node(s,'P6\n资产目录与授权回显',65,558,325,95),f=node(s,'PBIRS\n目录、报表、实际权限',865,558,350,95,C.navy,C.white);arrow(s,f,e,'left','right');text(s,'元数据读取',485,579,300,45,25,C.blue);}
 {let s=slide(p,'当前 Demo 已验证的能力与边界','测试服务已与 PBIRS 部署在同一台服务器，正式 P6 接口仍待接入',`依据：README.md；deploy-shared/verify.py、deploy-shared/verify_folders.py、tests/test_folder_policies.py。当前 P4 命名界面是测试 Demo，不代表正式 P6。停用撤销的是所管理的目录/报表资源权限，不等同于全局实时注销所有 PBIRS Cookie。原生旧 SOAP 接口仍有已知自定义授权兼容问题，未将其列为通过。本轮未更改 FullTrust。`);
 text(s,'已完成验证',65,202,520,50,30,C.green,true);text(s,'统一账号登录与免重复登录\niframe 报表展示\n目录浏览与目录 / 单报表授权\n改密、停用、启用与授权撤销\n新增下级报表自动应用目录授权',65,280,545,270,27);
 text(s,'下一步验证',720,202,490,50,30,C.blue,true);text(s,'正式 P6 认证与 IAM 对接\nRLS 模型角色与数据行隔离\n模型角色等扩展元数据\n正式域名、HTTPS 与会话治理',720,280,490,250,27);
 text(s,'截图中的 P4 名称沿用测试界面。现阶段结果证明集成方法可行，尚未等同于正式 P6 上线。',65,606,1140,65,22,C.muted);}
 {let s=slide(p,'正式接入 P6 的实施顺序','沿用已验证链路，替换 Demo 账号服务，再补齐数据级控制',`实施建议，非已完成事项。自定义认证需要维护扩展兼容性、密钥与 Cookie 安全。微软要求认证通信使用 TLS，见 ${SRC.auth}。P6 若使用 Keycloak，不应把任意浏览器传来的 subject 当成可信身份，应由现有认证上下文或服务端校验后的令牌签发桥接票据。版本升级、故障回滚、服务不可用时拒绝登录、审计、Cookie清理和集群 nonce 存储都需上线前验证。`);
 table(s,[['步骤','主要工作','验收结果'],['1  接入现有账号服务','替换 Demo 认证逻辑，使用稳定用户 ID','P6 新建用户可访问获授权内容'],['2  接入业务授权管理','目录 / 报表选择写入 PBIRS，记录审计','直链和内嵌权限一致，失败可核查'],['3  接入行级权限','报表模型定义规则，配置用户角色与范围','同报表不同用户只能看到自己的数据'],['4  完成部署与运维验证','HTTPS、浏览器策略、密钥、会话、升级兼容','目标浏览器通过，故障与回滚可执行']],65,204,1145,352,[245,520,380],22);
 text(s,'本次选择：P6 统一用户体系，PBIRS 自定义认证桥接，PBIRS 执行报表访问与模型安全',65,595,1140,69,26,C.navy,true);}
 {let s=slide(p,'参考资料与实现依据','官方能力与本项目验证结果分别说明',`完整来源：\n${Object.values(SRC).join('\n')}\n实现文件：README.md，server.py，ticket_auth.py，demo_admin.py，custom-security/P4Login.aspx，custom-security/P4Security.cs，deploy-shared/verify.py，deploy-shared/verify_folders.py。所有截图来自本次测试环境，非正式P6页面。`);
 text(s,'微软官方资料',65,202,1100,45,29,C.blue,true);
 text(s,'Power BI Report Server 开发指南与产品能力对比\nReporting Services 自定义认证与资源角色\nPower BI Report Server 行级安全（RLS）\nREST API：目录、资源策略、模型角色与成员分配',65,272,1135,216,27);
 text(s,'本项目验证依据',65,523,1100,45,29,C.blue,true);
 text(s,'共享 Demo 的用户管理、目录授权与报表内嵌页面\n统一登录、权限隔离、授权撤销及新增报表覆盖的实测记录',65,584,1135,82,24);
}
}
return {slides:p.slides.items.length};
}
