from __future__ import annotations

import html


FILE_REVIEW_MARKER_ID = "costerly-file-review-screen-active"
OBJECTS_MARKER_ID = "costerly-objects-screen-active"


def post_upload_transition_shell_html(
    *,
    title: str,
    subtitle: str | None = None,
    marker_id: str | None = None,
) -> str:
    """Return a lightweight full-screen shell for client-side screen transitions."""
    marker_html = ""
    if marker_id:
        marker_html = f'<div id="{html.escape(marker_id)}" style="display:none"></div>'

    subtitle_html = ""
    if subtitle:
        subtitle_html = (
            '<div class="post-upload-subtitle" '
            'style="color:rgba(42,31,44,0.58);font-family:\'IBM Plex Mono\',ui-monospace,'
            'SFMono-Regular,Menlo,Monaco,Consolas,monospace;font-size:22px;line-height:1.2;'
            'font-weight:700;letter-spacing:0.08em;text-transform:uppercase;margin-top:14px;'
            'white-space:nowrap;">'
            f'{html.escape(subtitle)}'
            '</div>'
        )

    return (
        '<div class="post-upload-stage" '
        'style="position:fixed;inset:0;z-index:2147483101;background:#F1EFEF;'
        'color:#2A1F2C;box-sizing:border-box;overflow:hidden;">'
        '<div class="post-upload-stage__inner" '
        'style="width:min(960px,calc(100vw - 56px));margin-left:auto;margin-right:auto;'
        'padding-top:42px;padding-bottom:72px;box-sizing:border-box;background:#F1EFEF;">'
        '<div class="post-upload-shell" style="width:100%;margin:0;padding:0;background:#F1EFEF;">'
        f'{marker_html}'
        '<h1 class="post-upload-title" '
        'style="font-family:\'IBM Plex Mono\',ui-monospace,SFMono-Regular,Menlo,Monaco,'
        'Consolas,monospace;color:#8049C6;font-size:40px;line-height:1.1;'
        'font-weight:500;letter-spacing:0;margin:0;padding:0;">'
        f'{html.escape(title)}'
        '</h1>'
        f'{subtitle_html}'
        '</div>'
        '</div>'
        '</div>'
    )
