"""Explicit native PBIRS export routes and user-scoped resource checks."""
import re
from demo_admin import AdminError

REPORT_OPERATION = re.compile(
    r'^/powerbi/api/explore/reports/'
    r'(?P<id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/'
    r'(?P<operation>querydata|conceptualschema|export/(?P<format>csv|xlsx))$', re.IGNORECASE)


def operation(path):
    match = REPORT_OPERATION.fullmatch(path)
    return match.groupdict() if match else None


def check_export_access(session, upstream, report_id):
    # The same user's NTLM session performs both the check and the export.
    response = session.get(upstream+'/Reports/api/v2.0/PowerBIReports('+report_id+')',
                           timeout=35, allow_redirects=False)
    if response.status_code in (403,404):
        raise AdminError(403, '当前用户没有此报表的导出权限')
    if response.status_code == 401:
        raise AdminError(409, 'Windows 报表凭据已失效，请联系管理员更新')
    if response.status_code != 200:
        raise AdminError(502, '无法核对报表权限，本次未执行导出')


def download_disposition(value):
    if value and not any(char in value for char in ('\r','\n','\0')):
        return value
    return None
