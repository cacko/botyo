from argparse import ArgumentTypeError
from botyo.server.output import to_mono
from botyo.server.socket.connection import Context
from botyo.server.models import EmptyResult, RenderResult
from .traceroute import Traceroute
from .dig import Dig
from .whois import WhoIs
from .tcptraceroute import TcpTraceroute
from botyo.server.blueprint import Blueprint
from botyo.server.models import ZMethod
from botyo.api.console.geo import Geo


bp = Blueprint("console")


@bp.command(method=ZMethod.CONSOLE_TRACEROUTE, desc="traceroute a host/ip")  # type: ignore
def traceroute_command(context: Context):
    try:
        traceroute = Traceroute(context.query)
        res = traceroute.text
        if not res:
            return EmptyResult()
        else:
            return RenderResult(method=ZMethod.CONSOLE_TRACEROUTE, message=res)
    except ArgumentTypeError:
        return RenderResult(message=to_mono("are you stupid?"))


@bp.command(method=ZMethod.CONSOLE_TCPTRACEROUTE, desc="tcptraceroute a host/ip")  # type: ignore
def tcptraceroute_command(context: Context):
    try:
        traceroute = TcpTraceroute(context.query)
        res = traceroute.text
        if not res:
            return EmptyResult()
        else:
            return RenderResult(method=ZMethod.CONSOLE_TCPTRACEROUTE, message=res)
    except ArgumentTypeError:
        return RenderResult(message=to_mono("are you stupid?"))


@bp.command(method=ZMethod.CONSOLE_DIG, desc="DNS lookup utility")  # type: ignore
def dig_command(context: Context):
    try:
        dig = Dig(context.query)
        res = dig.text
        if not res:
            return EmptyResult()
        else:
            return RenderResult(method=ZMethod.CONSOLE_DIG, message=res)
    except ArgumentTypeError:
        return RenderResult(message=to_mono("are you stupid?"))


@bp.command(
    method=ZMethod.CONSOLE_WHOIS,
    desc="Internet domain name and network number directory service",
)  # type: ignore
def whois_command(context: Context):
    try:
        whois = WhoIs(context.query)
        res = whois.text
        if not res:
            return EmptyResult()
        else:
            return RenderResult(method=ZMethod.CONSOLE_WHOIS, message=res)
    except ArgumentTypeError:
        return RenderResult(message=to_mono("are you stupid?"))


@bp.command(method=ZMethod.CONSOLE_GEO, desc="Geo info for given ip")  # type: ignore
def geo_command(context: Context):
    try:
        res = Geo(context.query).lookup()
        if not res:
            return EmptyResult()
        else:
            return RenderResult(method=ZMethod.CONSOLE_GEO, message=res)
    except ArgumentTypeError:
        return RenderResult(message=to_mono("are you stupid?"))
