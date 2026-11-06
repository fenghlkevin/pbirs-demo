export default async function({presentation:p}){
 const updates={
 'sh/sjahs3md':'方案修订稿    2026 年 11 月',
 'sh/5wzaxw32':'Power BI Report Server 是什么',
 'sh/fa50z65w':'本方案用 Power BI 报表承载业务看板',
 'sh/9gjahcz6':'身份集成的两种路线',
 'sh/zul8bqxo':'P6 管理账号，PBIRS 保存报表并执行访问检查',
 'sh/8ne98fyl':'验证身份、写入授权',
 'sh/wzm9cv6l':'从 P6 打开报表的登录流程',
 'sh/onqd07qt':'直接访问 PBIRS 的登录方式',
 'sh/bed4fidc':'报表内嵌效果',
 'sh/e9crulgf':'Demo 通过同源代理打开报表查看器，使用当前用户的 PBIRS 会话。',
 'sh/ql8jyx8b':'页面组织',
 'sh/wbux8nal':'资源权限与行级权限',
 'sh/t4vmdgnm':'已验证：目录与报表授权',
 'sh/83mlkbm1':'已验证：模型角色与数据行过滤',
 'sh/itszq5ob':'目录与报表授权',
 'sh/itszq5ob':'目录与报表授权',
 'sh/pwzqdg76':'在业务平台中管理报表授权',
 'sh/qx876l8r':'Demo 将授权写入 PBIRS，直接打开报表时同样检查权限',
 'sh/gfmho3id':'RLS 规则、角色和用户的关系',
 'sh/hgvix8zy':'RLS（行级安全）控制同一张报表中每个用户能看到的数据',
 'sh/7ad0ryhw':'报表模型\n角色及过滤规则',
 'sh/sbmhkji1':'Demo 授权\n绑定用户与角色',
 'sh/tcvitozm':'PBIRS 查询\n按当前用户过滤',
 'sh/kbatgb6t':'在 Desktop 定义角色和规则，随报表发布到 PBIRS',
 'sh/y9sbe1on':'读取已有角色，将选中的用户绑定写回 PBIRS',
 'sh/cnatcr6x':'模型执行行过滤，前端筛选器只用于交互',
 'sh/kb61sfy9':'同一报表的行级权限实测',
 'sh/lcfilkzu':'Province_RLS_Demo 使用 6 条合成数据，按 A、B 两个区域划分',
 'sh/jipgf2xw':'同一报表内，多角色授权会合并可见范围',
 'sh/ixgfmhwr':'修改 demo1 的角色后，查询金额从 A 区 600 变为 B 区 1,500。',
 'sh/c7e1wryp':'移除全部模型角色后，测试用户无法查询数据。测试结束已恢复原始分配。',
 'sh/ylcnux03':'接口可读取资产目录、资源策略和模型角色，供 P6 展示与授权使用',
 'sh/3mp4by98':'P6 业务角色与 PBIRS 模型角色分别维护。映射以报表 ID 和模型角色 ID 为准。',
 'sh/90fex0by':'账号与权限的管理分工',
 'sh/mdovmlc7':'账号在 P6 维护，报表模型在 PBIRS 维护，授权通过接口写入并核对',
 'sh/kzytgr2h':'Demo 验证结果与正式接入工作',
 'sh/l07upwjm':'Demo 与 PBIRS 部署在同一台测试服务器，尚未接入正式 P6',
 'sh/ze18ri1c':'系统账号登录与报表免重复登录\niframe 展示、目录与单报表授权\n用户创建、改密、停用与启用\n全部 RLS 角色读取、跨报表批量授权\n不同用户的数据行隔离',
 'sh/edsrid0r':'正式接入工作',
 'sh/1g3qt8zi':'P6 认证与 IAM 接口对接\n业务角色到模型角色的映射\n权限变更审计、失败重试与核对\nHTTPS、会话及版本升级验证',
 'sh/0fa9knix':'测试界面沿用 P4 名称。当前实现管理用户与 RLS 的直接绑定，业务角色映射尚未开发。',
 'sh/z2dovy9o':'复用已验证的认证与授权接口，接入 P6 现有账号和业务角色',
 'sh/ix87ex87':'报表访问沿用当前用户身份，P6 管理授权，PBIRS 执行访问检查与行过滤'
 };
 for(const [id,text] of Object.entries(updates))p.resolve(id).text=text;
 const t=p.resolve('tb/iho3mxwn');t.insertRows({index:3,count:1});const vals=[['用户','模型角色','可见数据','金额合计'],['demo1','Province_A','A 区 3 条','600'],['demo2','Province_B','B 区 3 条','1,500'],['demo3','Province_A、Province_B','全部 6 条','2,100']];for(let r=0;r<4;r++)for(let c=0;c<4;c++)t.cells.set(r,c,vals[r][c]);t.position={...t.position,height:245};
 p.resolve('tb/v2dofe58').cells.set(3,2,'已验证读取与成员写回');
 const roadmap=p.resolve('tb/2p8bmd8z');roadmap.cells.set(3,1,'复用用户绑定接口，增加业务角色映射与同步');roadmap.cells.set(3,2,'角色成员变化后，对应用户的 RLS 分配同步生效');
 const sources='微软 RLS 文档：https://learn.microsoft.com/en-us/power-bi/report-server/row-level-security-report-server\nPBIRS REST API：https://learn.microsoft.com/en-us/rest/api/power-bi-report/power-bi-reports\n项目证据：rls-demo/README.md、rls-management/README.md、verify_batch.py。测试为 Import 合成数据模型，不将结果扩大到所有数据源连接方式。';
 p.slides.getItem(12).speakerNotes.text=sources+'\n模型角色和规则按模型维护，不是为每个用户新建规则。当前演示为静态区域角色。动态 RLS 可通过用户与区域关系表扩展，须单独设计数据关系并验证。自定义认证成员按显式用户标识分配。';
 p.slides.getItem(13).speakerNotes.text=sources+'\n实测 demo1 A区3条600，demo2 B区3条1500，demo3全部6条2100。多角色可见范围叠加。';
 p.slides.getItem(14).speakerNotes.text=sources;
 const old=p.slides.items.map(s=>s.toSnapshot().aid);const added=[];
 const ink='#082E5C',muted='#516D89';
 function text(s,value,x,y,w,h,size=24,bold=false,color=ink){const a=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{width:0,fill:'none'}});a.text=value;a.text.style={fontFamily:'Arial',fontSize:size,bold,color};return a}
 function slide(title,sub){const s=p.slides.add();s.background.fill='#FFFFFF';text(s,title,64,44,1150,65,34,true);text(s,sub,66,118,1140,70,22,false,muted);added.push(s.toSnapshot().aid);return s}
 function table(s,values,top,widths,height){const t=s.tables.add({rows:values.length,columns:values[0].length,left:65,top,width:1150,height,columnWidths:widths,values});for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){const a=t.getCell(r,c);a.fill=r===0?ink:(r%2?'#EDF4FB':'#FFFFFF');a.text.style={fontFamily:'Arial',fontSize:22,color:r===0?'#FFFFFF':ink,bold:r===0};}t.borders.assign({fill:'#CBDCEC',width:1,style:'solid'});return t}
 let s=slide('Demo 中的行级权限授权','选一个用户，在全部模型角色列表中勾选，点击“保存全部修改”');
 s.images.add({path:'/path/to/pbirs-demo/rls-management/batch-roles.png',position:{left:160,top:188,width:960,height:504}});s.speakerNotes.text='测试系统实际页面截图。已绑定角色自动勾选，角色旁显示所属报表。已实测跨两张报表一次提交和恢复。读取失败的报表不参与保存。资源查看授权仍需单独配置。';
 s=slide('一次保存时，后台如何处理','页面统一提交，后台按报表分别写入 PBIRS');
 table(s,[['步骤','后台处理'],['读取','获取所有报表的角色，以及当前用户已有的绑定'],['计算','只提交勾选有变化的报表，保留其他用户的成员分配'],['写入','检查角色归属与版本，再调用成员分配接口'],['核对','回读 PBIRS，逐张显示成功或失败']],218,[190,960],310);
 text(s,'PBIRS 不支持跨报表事务，部分失败时保留未确认的勾选，并提示重新读取核对。',66,568,1135,80,23);s.speakerNotes.text=sources+'\n实际接口 GET /api/admin/rls/user 与 POST /api/admin/rls/batch。PBIRS GET DataModelRoles、GET/PUT DataModelRoleAssignments。Demo 写操作串行化，使用 revision 与写前重读检测冲突。原生接口没有 CAS，外部并发修改仍有极小竞态，正式环境须控制多入口并行编辑。';
 s=slide('通过业务角色分配 RLS','后续设计：业务角色关联模型角色，后台展开到具体用户');
 table(s,[['P6 业务角色','角色成员','绑定的模型角色'],['A 区业务员','demo1、demo2','报表甲 / Province_A\n报表乙 / Region_A']],224,[260,320,570],175);
 text(s,'PBIRS 最终保存的成员分配',66,438,1100,45,26,true);
 text(s,'报表甲的 Province_A：demo1、demo2\n报表乙的 Region_A：demo1、demo2',66,497,1100,100,26);
 text(s,'当前 Demo 已实现“用户与 RLS 直接绑定”。业务角色映射和自动展开尚未开发。',66,620,1120,48,21,false,muted);s.speakerNotes.text='这是基于现有直接绑定接口的扩展设计，未实现，不是 PBIRS 自动读取 P6 业务角色。角色名称为解释用途的示例。模型角色按所属报表分别存在。自定义认证按具体用户标识写入成员关系。';
 s=slide('业务角色变化后的权限同步','同步用户与模型角色的分配，报表数据无需因此重新刷新');
 table(s,[['管理操作','需要同步的范围'],['业务角色新增或移除 RLS 绑定','重新计算该角色全部成员的有效授权'],['用户加入或退出业务角色','重新计算受影响用户的授权'],['一个用户拥有多个业务角色','合并所有来源，撤销时保留其他来源仍授予的权限'],['同步失败或报表重新发布','记录失败、重新读取模型角色、核对并重试']],218,[450,700],325);
 text(s,'P6 维护授权来源。PBIRS 保存最终用户分配，不需要复制用户密码。',66,585,1130,65,24,true);s.speakerNotes.text='后续设计，尚未实现业务角色层。同步应按受影响用户与报表增量计算，避免全量覆盖无关成员。规则变更涉及模型重发和重新验证，成员分配变更不等于数据刷新。正式实现须增加审计、重试、幂等和停用后的授权撤销。';
 p.slides.reorder([...old.slice(0,14),...added,...old.slice(14)]);
 for(let i=0;i<p.slides.items.length;i++){const sl=p.slides.getItem(i);if(i===0)continue;const snap=sl.toSnapshot();const footer=snap.shapes.find(x=>/^\d{2}$/.test(x.text||'')&&x.frame.top>650);if(footer)p.resolve(footer.aid).text=String(i+1).padStart(2,'0');else text(sl,String(i+1).padStart(2,'0'),1170,666,50,28,14,false,muted);}
 await p.render({montage:true});return {slides:p.slides.items.length};
}
