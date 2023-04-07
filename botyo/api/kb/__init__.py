from botyo.server.blueprint import Blueprint
from botyo.server.models import EmptyResult, RenderResult
from botyo.kb import KnowledgeBase
from botyo.server.socket.connection import Context
from botyo.server.output import TextOutput
from emoji import emojize
from enum import Enum
import logging
from botyo.chatyo import getResponse, Payload

from botyo.server.models import ZMethod

bp = Blueprint("kb")


class ICONS(Enum):
    GLASSES = emojize(":glasses:")
    LIGHTBULD = emojize(":light_bulb:")
    OPENBOOK = emojize(":open_book:")
    QUESTION = emojize(":information:")


@bp.command(
    method=ZMethod.KNOWLEDGE_ARTICLE,
    desc="search and displayed the first match for a term from wikipedia",
    icon="library_books"
)  # type: ignore
def article_command(context: Context):
    try:
        assert context.query
        wiki = KnowledgeBase(context.query)
        article = wiki.summary
        article = f"{ICONS.OPENBOOK.value} {article}"
        TextOutput.addRows(article.split("\n"))
        return RenderResult(
            message=TextOutput.render(), method=ZMethod.KNOWLEDGE_ARTICLE
        )
    except (FileNotFoundError, AssertionError):
        return EmptyResult(method=ZMethod.KNOWLEDGE_ARTICLE)


@bp.command(
    method=ZMethod.KNOWLEDGE_ASK,
    desc="ask to learn",
    icon="question_answer"
)  # type: ignore
def bard_command(context: Context):
    msg = context.query
    if not msg:
        return None
    json = getResponse("text/bard", Payload(message=msg, source=context.source))
    res = RenderResult(message=json.response, method=ZMethod.KNOWLEDGE_ASK)
    return res


@bp.command(
    method=ZMethod.KNOWLEDGE_TELL,
    desc="ask to be told",
    icon="short_text"
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
    icon="contact_support"
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
