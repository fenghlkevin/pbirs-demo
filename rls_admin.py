"""PBIRS is the source of model roles and assignments; no duplicate role store."""
import copy
import hashlib
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from demo_admin import AdminError, Policies, is_admin, public_user


def canonical(assignments):
    return sorted((a['GroupUserName'],tuple(sorted(set(a.get('DataModelRoles',[])))))
                  for a in assignments)


def revision(roles,assignments):
    value={'roles':sorted((r['ModelRoleId'],r['ModelRoleName']) for r in roles),
           'assignments':canonical(assignments)}
    return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()


class RlsAdmin:
    def __init__(self,policies=None):
        self.policies=policies or Policies()

    def reports(self):
        return [r for r in self.policies.catalog() if r['Type']=='PowerBIReport']

    def inventory(self,accounts):
        reports=self.reports()
        def scan(report):
            try:
                # Independent sessions per worker: requests.Session is not thread-safe.
                worker=Policies()
                roles=worker.call('GET','/PowerBIReports('+report['Id']+')/DataModelRoles').get('value',[])
                return {**report,'roles':[{'Id':r['ModelRoleId'],'Name':r['ModelRoleName']} for r in roles],
                        'status':'ok','error':None}
            except Exception:
                return {**report,'roles':[],'status':'error','error':'读取失败，请重试或检查报表模型'}
        with ThreadPoolExecutor(max_workers=4) as pool:
            results=list(pool.map(scan,reports))
        return {'reports':results,'users':[public_user(name,a) for name,a in accounts.items() if not is_admin(a)],
                'roleCount':sum(len(r['roles']) for r in results),
                'failedCount':sum(r['status']=='error' for r in results)}

    def report(self,report_id):
        try:
            if not isinstance(report_id,str) or str(uuid.UUID(report_id))!=report_id.lower():raise ValueError()
        except (ValueError,AttributeError):raise AdminError(400,'报表 ID 不正确')
        report=next((r for r in self.reports() if r['Id'].lower()==report_id.lower()),None)
        if not report:raise AdminError(404,'Power BI 报表不存在')
        return report

    def read(self,report_id):
        report=self.report(report_id)
        prefix='/PowerBIReports('+report['Id']+')'
        roles=self.policies.call('GET',prefix+'/DataModelRoles').get('value',[])
        assignments=self.policies.call('GET',prefix+'/DataModelRoleAssignments').get('value',[])
        return report,roles,assignments

    def view(self,report_id,accounts):
        report,roles,assignments=self.read(report_id)
        policy=self.policies.read(self.policies.policy_path(report))
        can_view={a['GroupUserName'] for a in policy['Policies'] if any(
            r['Name'] in ('Browser','Content Manager','Publisher','Report Builder','My Reports')
            for r in a.get('Roles',[]))}
        users=[{**public_user(name,account),'hasReportAccess':account['principal'] in can_view}
               for name,account in accounts.items() if not is_admin(account)]
        names={a['principal']:(name,a) for name,a in accounts.items()}
        bindings=[]
        for item in assignments:
            principal=item['GroupUserName'];found=names.get(principal)
            bindings.append({'principal':principal,'roleIds':item.get('DataModelRoles',[]),
                'username':found[0] if found else None,
                'displayName':found[1].get('displayName',found[0]) if found else principal,
                'protected':not found or is_admin(found[1])})
        return {'report':report,'roles':[{'Id':r['ModelRoleId'],'Name':r['ModelRoleName']} for r in roles],
                'assignments':bindings,'users':users,'revision':revision(roles,assignments)}

    def save(self,data,accounts,validate_only=False):
        if not isinstance(data,dict):raise AdminError(400,'请求内容不正确')
        name=data.get('username');account=accounts.get(name) if isinstance(name,str) else None
        if not account:raise AdminError(404,'用户不存在')
        if is_admin(account):raise AdminError(400,'管理员的模型角色受保护，此页面只管理普通用户')
        if not account.get('enabled',True):raise AdminError(400,'请先启用用户再修改行级权限')
        selected=data.get('roleIds')
        if not isinstance(selected,list) or len(selected)>1000 or any(not isinstance(i,str) for i in selected):
            raise AdminError(400,'请选择正确的模型角色列表')
        report,roles,assignments=self.read(data.get('reportId'))
        if data.get('revision')!=revision(roles,assignments):
            raise AdminError(409,'PBIRS 的角色或成员已变化，请重新读取后确认再保存')
        known={r['ModelRoleId'] for r in roles};desired=set(selected)
        if not desired<=known:raise AdminError(400,'选中的角色不属于当前报表，请重新读取 PBIRS 角色')
        if validate_only:return None
        principal=account['principal']
        merged=[copy.deepcopy(a) for a in assignments if a['GroupUserName']!=principal]
        if desired:merged.append({'GroupUserName':principal,'DataModelRoles':sorted(desired)})
        if canonical(assignments)!=canonical(merged):
            prefix='/PowerBIReports('+report['Id']+')'
            # Re-read immediately before the full-list replacement. The HTTP handler
            # serializes Demo writes; PBIRS has no conditional revision/CAS endpoint.
            latest_roles=self.policies.call('GET',prefix+'/DataModelRoles').get('value',[])
            latest=self.policies.call('GET',prefix+'/DataModelRoleAssignments').get('value',[])
            if revision(latest_roles,latest)!=revision(roles,assignments):
                raise AdminError(409,'PBIRS 的角色或成员已变化，请重新读取后确认再保存')
            try:self.policies.call('PUT',prefix+'/DataModelRoleAssignments',merged)
            except Exception as error:
                raise AdminError(502,'PBIRS 角色写入未确认，请重新读取实际分配后再操作') from error
            actual=self.policies.call('GET',prefix+'/DataModelRoleAssignments').get('value',[])
            if canonical(actual)!=canonical(merged):
                raise AdminError(409,'PBIRS 保存后的分配与预期不一致，请重新读取并核对')
        return self.view(report['Id'],accounts)

    def user_inventory(self,username,accounts):
        account=accounts.get(username)
        if not account or is_admin(account):raise AdminError(400,'请选择普通用户')
        results=[]
        for report in self.reports():
            try:
                _,roles,assignments=self.read(report['Id'])
                selected=next((a.get('DataModelRoles',[]) for a in assignments
                               if a['GroupUserName']==account['principal']),[])
                results.append({**report,'status':'ok','roles':[{'Id':r['ModelRoleId'],'Name':r['ModelRoleName']} for r in roles],
                                'roleIds':selected,'revision':revision(roles,assignments)})
            except Exception:
                results.append({**report,'status':'error','roles':[],'error':'读取失败，未修改此报表'})
        return {'user':public_user(username,account),'reports':results}

    def save_many(self,data,accounts):
        if not isinstance(data,dict) or not isinstance(data.get('changes'),list):
            raise AdminError(400,'请求内容不正确')
        changes=data['changes']
        if not changes or len(changes)>1000 or any(not isinstance(c,dict) for c in changes):
            raise AdminError(400,'请选择需要保存的角色')
        ids=[c.get('reportId') for c in changes]
        if any(not isinstance(i,str) for i in ids) or len(set(ids))!=len(ids):
            raise AdminError(400,'报表列表不正确或重复')
        payloads=[{**c,'username':data.get('username')} for c in changes]
        # Validate the complete batch before any writes. PBIRS does not provide
        # cross-report transactions; failures during writes are returned per item.
        for payload in payloads:self.save(payload,accounts,validate_only=True)
        results=[]
        for payload in payloads:
            try:
                actual=self.save(payload,accounts)
                results.append({'reportId':payload['reportId'],'status':'saved','data':actual})
            except Exception as error:
                results.append({'reportId':payload['reportId'],'status':'error',
                                'error':str(error) if isinstance(error,AdminError) else '保存未确认，请重新读取核对'})
        return {'results':results,'complete':all(r['status']=='saved' for r in results)}
