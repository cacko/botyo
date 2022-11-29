from botyo_server.blueprint import Blueprint
from botyo_server.models import EmptyResult, RenderResult
from app.kb import KnowledgeBase
from botyo_server.socket.connection import Context
from botyo_server.output import TextOutput
from emoji import emojize
from enum import Enum
import logging

from app.api import ZMethod

bp = Blueprint("kb")


class ICONS(Enum):
    GLASSES = emojize(":glasses:")
    LIGHTBULD = emojize(":light_bulb:")
    OPENBOOK = emojize(":open_book:")
    QUESTION = emojize(":information:")


@bp.command(
    method=ZMethod.KNOWLEDGE_ARTICLE,
    desc="search and displayed the first match for a term from wikipedia",
)  # type: ignore
def article_command(context: Context):
    try:
        wiki = KnowledgeBase(context.query)
        article = wiki.summary
        article = f"{ICONS.OPENBOOK.value} {article}"
        TextOutput.addRows(article.split("\n"))
        return RenderResult(
            message=TextOutput.render(), method=ZMethod.KNOWLEDGE_ARTICLE
        )
    except FileNotFoundError:
        return EmptyResult(method=ZMethod.KNOWLEDGE_ARTICLE)


@bp.command(
    method=ZMethod.KNOWLEDGE_ASK,
    desc="ask to learn",
)  # type: ignore
def ask_command(context: Context):
    try:
        msg = context.query
        if not msg:
            return None
        answer = KnowledgeBase.answer(msg)
        res = RenderResult(
            message=f"{ICONS.LIGHTBULD.value} {answer.response}"
            if answer.response
            else None,
            attachment=answer.attachment,
            method=ZMethod.KNOWLEDGE_ASK,
        )
        return res
    except FileNotFoundError:
        return EmptyResult(method=ZMethod.KNOWLEDGE_ASK)
    except Exception as e:
        logging.error(e)


@bp.command(
    method=ZMethod.KNOWLEDGE_TELL,
    desc="ask to be told",
)  # type: ignore
def tell_command(context: Context):
    try:
        title = context.query
        if not title:
            return None
        summarized = KnowledgeBase.summarized(title)
        return RenderResult(
            message=f"{ICONS.GLASSES.value} {summarized.response}",
            method=ZMethod.KNOWLEDGE_TELL,
        )
    except FileNotFoundError:
        return EmptyResult(method=ZMethod.KNOWLEDGE_TELL)
    except Exception as e:
        logging.error(e)


@bp.command(
    method=ZMethod.KNOWLEDGE_WTF,
    desc="wtf is that",
)  # type: ignore
def wtf_command(context: Context):
    try:
        title = context.query
        if not title:
            return None
        answer = KnowledgeBase.wolfram(title)
        return RenderResult(
            message=f"{ICONS.QUESTION.value} {answer.response}"
            if answer.response
            else None,
            attachment=answer.attachment,
            method=ZMethod.KNOWLEDGE_WTF,
        )
    except FileNotFoundError:
        return EmptyResult(method=ZMethod.KNOWLEDGE_WTF)
