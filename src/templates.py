blame_phantom_html_template = """
    <body id="inline-git-blame">
        <style>{css}</style>
        <div class="phantom-arrow"></div>
        <div class="phantom">
            <span class="message">
                <strong>Git Blame</strong> ({user})
                {date} {time} |
                <a href="prev-{sha}+{sha_skip_list}">[Prev]</a>
                {sha}
                <a href="copy-{sha}">[Copy]</a>
                <a href="show-{sha}">[Show]</a>
                <a class="close" href="close">\u00D7</a>
            </span>
        </div>
    </body>
"""

blame_phantom_css = """
    div.phantom-arrow {
        border-top: 0.4rem solid transparent;
        border-left: 0.5rem solid color(var(--bluish) blend(var(--background) 30%));
        width: 0;
        height: 0;
    }
    div.phantom {
        padding: 0.4rem 0 0.4rem 0.7rem;
        margin: 0 0 0.2rem;
        border-radius: 0 0.2rem 0.2rem 0.2rem;
        background-color: color(var(--bluish) blend(var(--background) 30%));
    }
    div.phantom span.message {
        padding-right: 0.7rem;
    }
    div.phantom a {
        text-decoration: inherit;
    }
    div.phantom a.close {
        padding: 0.35rem 0.7rem 0.45rem 0.8rem;
        position: relative;
        bottom: 0.05rem;
        border-radius: 0 0.2rem 0.2rem 0;
        font-weight: bold;
    }
    html.dark div.phantom a.close {
        background-color: #00000018;
    }
    html.light div.phantom a.close {
        background-color: #ffffff18;
    }
"""

# ------------------------------------------------------------

blame_all_phantom_html_template = """
    <body id="inline-git-blame">
        <style>{css}</style>
        <div class="phantom">
            <span class="message">
                {sha} (<span class="user">{user}</span> {date} {time})
                <a class="close" href="close">\u00D7</a>
            </span>
        </div>
    </body>
"""


blame_all_phantom_css = """
    div.phantom {
        padding: 0;
        margin: 0;
        background-color: color(var(--bluish) blend(var(--background) 30%));
    }
    div.phantom .user {
        width: 10em;
    }
    div.phantom a.close {
        padding: 0.35rem 0.7rem 0.45rem 0.8rem;
        position: relative;
        bottom: 0.05rem;
        font-weight: bold;
    }
    html.dark div.phantom a.close {
        background-color: #00000018;
    }
    html.light div.phantom a.close {
        background-color: #ffffff18;
    }
"""
