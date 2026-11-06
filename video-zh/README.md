# 中文方案视频初版

最终成片：output/P6与PBIRS集成方案_中文版.mp4，1920×1080、24fps、约7分06秒。带中文旁白、烧录字幕和15个MP4章节。

讲解沿用方案逻辑：PBIRS基本概念、AD与自定义认证、同机部署及接口分工、身份票据与会话、直接登录、用户管理、iframe内嵌、资源权限、目录授权、模型RLS规则、跨报表用户绑定、区域数据隔离实测、后续业务角色映射、PBIRS改动。

实际页面来自本项目截图与本次已授权浏览器采集。动画表示流程原理，并非连续操作录屏。RLS数据示意采用测试合成数据。业务角色自动展开明确标为后续设计。没有把密码、密钥或内部访问地址放入视频和旁白。

配音：zh-CN-XiaoxiaoNeural，中文合成语音。外部配音最初被自动审核拒绝；用户随后明确允许将不含密码、密钥及内部地址的脱敏旁白发送至微软Edge在线语音服务。本次只制作中文版本，葡语及英语版等待用户审阅后另行推进。

script.tsv / script.json 为旁白，render.py 生成页面与动态图，finalize.py 调整音量、写入章节并完整解码检查。字幕在 output/中文字幕.srt。检查结果 output/validation.json。

技术内容依据项目 README.md、rls-demo/README.md、rls-management/README.md、bilingual/README.md、portal-nav-fix/README.md 及已有PPT。视频保留了权限同步与继承窗口、跨报表非事务等现有限制的说明。截图中的业务字段名沿用真实测试页面，不对其作自动翻译。
