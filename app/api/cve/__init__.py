from app.api.cve.cve import CVE
from app.api.cve.subscription import Subscription
from botyo_server.blueprint import Blueprint
from botyo_server.output import TextOutput
from botyo_server.models import RenderResult, EmptyResult
from botyo_server.socket.connection import Context
from app.api import ZMethod


bp = Blueprint("cve")


@bp.command(method=ZMethod.CVE_CVE, desc="Latest Common Vulnerabilities and Exposures.")  # type: ignore
def cve_command(context: Context) -> RenderResult:
    try:
        cve = CVE(context.query)
        message = cve.message
        return RenderResult(message=message, method=ZMethod.CVE_CVE)
    except AssertionError:
        return EmptyResult()


# @bp.command(method=ZMethod.CVE_ALERT, desc="subscribe for CVE updates")  # type: ignore
# def cvesubscribe_command(context: Context) -> RenderResult:
#     if any([not context.client, not context.group, not context.query]):
#         return EmptyResult()
#     sub = Subscription(context.client, context.group, context.query)
#     sub.schedule()
#     return RenderResult(
#         method=ZMethod.CVE_ALERT, message=f"Subscribed for {sub.subscription_name}"
#     )


# @bp.command(method=ZMethod.CVE_UNALERT, desc="unsubscribe for CVE updates")  # type: ignore
# def cveunsubscribe_command(context: Context) -> RenderResult:
#     if any([not context.client, not context.group, not context.query]):
#         return EmptyResult()
#     sub = Subscription(context.client, context.group, context.query)
#     try:
#         sub.cancel()
#         return RenderResult(
#             method=ZMethod.CVE_UNALERT,
#             message=f"Unsubscribed for {sub.subscription_name}",
#         )

#     except Exception:
#         return EmptyResult()


# @bp.command(
#     method=ZMethod.CVE_LISTALERTS, desc="list current subscrionts for CVE updates"
# )  # type: ignore
# def cvelistsubscriptions_command(context: Context) -> RenderResult:
#     if any([not context.client, not context.group]):
#         return EmptyResult()
#     jobs = Subscription.forGroup(context.client, context.group)
#     if not jobs:
#         return RenderResult(method=ZMethod.CVE_LISTALERTS, message="No subscriptions")

#     TextOutput.addRows(map(lambda x: x.name, jobs))
#     return RenderResult(method=ZMethod.CVE_LISTALERTS, message=TextOutput.render())
