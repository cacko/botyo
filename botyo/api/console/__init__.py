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
from botyo.api.console.geo import GeoCoder, GeoIP


bp = Blueprint("console")


@bp.command(
    method=ZMethod.CONSOLE_TRACEROUTE,
    desc="traceroute a host/ip",
    icon="turn_sharp_right")  # type: ignore
def traceroute_command(context: Context):
    try:
        assert context.query
        traceroute = Traceroute(context.query)
        res = traceroute.text
        if not res:
            return EmptyResult()
        else:
            return RenderResult(method=ZMethod.CONSOLE_TRACEROUTE, message=res)
    except ArgumentTypeError:
        return RenderResult(message=to_mono("are you stupid?"))


@bp.command(
    method=ZMethod.CONSOLE_TCPTRACEROUTE,
    desc="tcptraceroute a host/ip",
    icon="roundabout_right")  # type: ignore
def tcptraceroute_command(context: Context):
    try:
        assert context.query
        traceroute = TcpTraceroute(context.query)
        res = traceroute.text
        if not res:
            return EmptyResult()
        else:
            return RenderResult(method=ZMethod.CONSOLE_TCPTRACEROUTE, message=res)
    except ArgumentTypeError:
        return RenderResult(message=to_mono("are you stupid?"))


@bp.command(
    method=ZMethod.CONSOLE_DIG,
    desc="DNS lookup utility",
    icon="dns")  # type: ignore
def dig_command(context: Context):
    try:
        assert context.query
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
    icon="alternate_email"
)  # type: ignore
def whois_command(context: Context):
    try:
        assert context.query
        whois = WhoIs(context.query)
        res = whois.text
        if not res:
            return EmptyResult()
        else:
            return RenderResult(method=ZMethod.CONSOLE_WHOIS, message=res)
    except ArgumentTypeError:
        return RenderResult(message=to_mono("are you stupid?"))


@bp.command(
    method=ZMethod.CONSOLE_GEOIP,
    desc="Geo info for given ip",
    icon="public")  # type: ignore
def geo_command(context: Context):
    try:
        assert context.query
        res = GeoIP(context.query).lookup()
        if not res:
            return EmptyResult()
        else:
            return RenderResult(method=ZMethod.CONSOLE_GEOIP, message=res)
    except ArgumentTypeError:
        return RenderResult(message=to_mono("are you stupid?"))


@bp.command(
    method=ZMethod.CONSOLE_GEOCODER,
    desc="Geo info for given address or gps",
    icon="public")  # type: ignore
def geocoder_command(context: Context):
    try:
        assert context.query
        res = GeoCoder(context.query).lookup()
        if not res:
            return EmptyResult()
        else:
            return RenderResult(method=ZMethod.CONSOLE_GEOCODER, message=res)
    except ArgumentTypeError:
        return RenderResult(message=to_mono("are you stupid?"))
