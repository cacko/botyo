from botyo.server.blueprint import Blueprint
from botyo.server.output import to_mono
from botyo.server.models import Attachment, EmptyResult, RenderResult
from botyo.server.socket.connection import Context
from botyo.server.models import ZMethod
from botyo.music.song import Song
from botyo.music.albumart import AlbumArt
from botyo.music.lyrics import Lyrics
from botyo.music.nowplay import Track
import logging

bp = Blueprint("music")


@bp.command(
    method=ZMethod.MUSIC_SONG,
    desc="searches for song and attaches it",
    icon="audiotrack")  # type: ignore
def song_command(context: Context) -> RenderResult:
    try:
        assert context.query
        assert len(context.query.strip()) > 4
        song = Song(context.query)
        path = song.destination
        message = song.message
        logging.warning(path)
        logging.warning(song)
        res = RenderResult(
            message=message,
            attachment=Attachment(
                path=path.as_posix(),
                contentType=song.content_type,
                duration=song.duration
            ),
            method=ZMethod.MUSIC_SONG,
        )
        return res
    except FileNotFoundError:
        return EmptyResult()
    except Exception as e:
        logging.exception(e)
        return EmptyResult()


@bp.command(
    method=ZMethod.MUSIC_ALBUMART,
    desc="album art",
    icon="album")  # type: ignore
def albumart_command(context: Context) -> RenderResult:
    try:
        assert context.query
        assert len(context.query.strip()) > 1
        albumart = AlbumArt(context.query)
        path = albumart.destination
        assert path
        res = RenderResult(
            attachment=Attachment(
                path=path.as_posix(), contentType="image/png"),
            method=ZMethod.MUSIC_ALBUMART,
        )
        return res
    except AssertionError as e:
        logging.error(e)
        return EmptyResult()


@bp.command(
    method=ZMethod.MUSIC_LYRICS,
    desc="dump lyrics of a song",
    icon="lyrics")  # type: ignore
def lyrics_command(context: Context) -> RenderResult:
    try:
        assert context.query
        assert len(context.query.strip()) > 1
        lyrics = Lyrics(context.query)
        message = lyrics.text
        assert message
        res = RenderResult(message=to_mono(message), method=ZMethod.MUSIC_LYRICS)
        return res
    except AssertionError as e:
        logging.error(e)
        return EmptyResult()


@bp.command(
    method=ZMethod.MUSIC_NOWPLAYING_SONG,
    desc="current song playing",
    icon="speaker")  # type: ignore
def nowplaying_song_command(context: Context) -> RenderResult:
    try:
        track = Track.trackdata
        assert track
        return RenderResult(
            message=track.message,
            attachment=Attachment(
                path=track.audio_destination.as_posix(),
                contentType=track.audio_content_type,
            ),
            method=ZMethod.MUSIC_NOWPLAYING_SONG,
        )
    except Exception as e:
        logging.error(e)
        return EmptyResult()


@bp.command(
    method=ZMethod.MUSIC_NOWPLAYING_ART,
    desc="current album art playing",
    icon="playlist_add_check_circle")  # type: ignore
def nowplaying_art_command(context: Context) -> RenderResult:
    try:
        track = Track.trackdata
        assert track
        return RenderResult(
            message=track.message,
            attachment=Attachment(
                path=track.album_art.as_posix(),
                contentType=track.art_content_type,
            ),
            method=ZMethod.MUSIC_NOWPLAYING_ART,
        )
    except Exception as e:
        logging.error(e)
        return EmptyResult()
