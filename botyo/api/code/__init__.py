from botyo.code import Code
from botyo.server.blueprint import Blueprint
from botyo.server.socket.connection import Context
from botyo.server.models import RenderResult
from botyo.server.models import ZMethod


bp = Blueprint("code")


@bp.command(
    method=ZMethod.CODE_PHP,
    desc="Generates sample PHP code by given instructions",
    icon="php"
)  # type: ignore
def php_command(context: Context):
    msg = context.query
    if not msg:
        return None
    resp = Code.php(text=msg)
    res = RenderResult(message=resp.response, method=ZMethod.CODE_PHP, plain=True)
    return res


@bp.command(
    method=ZMethod.CODE_PYTHON,
    desc="Generates sample Python code by given instructions",
    icon="source"
)  # type: ignore
def python_command(context: Context):
    msg = context.query
    if not msg:
        return None
    resp = Code.python(text=msg)
    res = RenderResult(message=resp.response, method=ZMethod.CODE_PYTHON, plain=True)
    return res
