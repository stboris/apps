#!/usr/bin/env python3
"""Split one bilingual (de/en) page into two real pages, one URL per language, for search engines.

    python3 tools/bilingual.py SRC.html OUT_DIR BASE_URL DEFAULT_LANG

Writes OUT_DIR/index.html (DEFAULT_LANG, served at BASE_URL) and OUT_DIR/<other>/index.html
(served at BASE_URL<other>/). Used by every site: apps.borisstiner.com (default en),
lina-kreideheldin.ch (default de), later lina-kreideheldin.ch/zaehlis/ etc.

Source conventions:
- Any element with lang="de" / lang="en" is kept only in its language's page (also <title>, <meta>, JSON-LD <script>).
- alt / aria-label / title attributes written "German / English" keep only their half.
- {{url}} = this page's URL, {{url:de}} / {{url:en}} = the URL of each language version.
- <!--alternates--> in <head> becomes canonical + hreflang links + og:url + og:locale.
- <details><summary>Q</summary>A</details> blocks become a FAQPage JSON-LD automatically.
- A link whose href is the current page's URL gets aria-current="page" (use it for the DE/EN switch).
"""
import html as htmllib
import json
import os
import re
import sys

LANGS = ('de', 'en')
LOCALE = {'de': 'de_CH', 'en': 'en_GB'}
VOID = {'meta', 'link', 'img', 'br', 'hr', 'input', 'source'}


def strip_lang(s, drop):
    """Remove every element carrying lang="<drop>", including its content."""
    opener = re.compile(r'<(\w+)\b[^>]*\blang="%s"[^>]*>' % drop)
    while True:
        m = opener.search(s)
        if not m:
            return s
        tag = m.group(1).lower()
        end = m.end()
        if tag not in VOID:
            depth, pos = 1, m.end()
            tok = re.compile(r'<(/?)%s\b[^>]*>' % tag, re.I)
            while depth:
                t = tok.search(s, pos)
                assert t, 'unclosed <%s lang="%s"> near: %s' % (tag, drop, s[m.start():m.start() + 80])
                depth += -1 if t.group(1) else 1
                pos = t.end()
            end = pos
        # drop the line too if the element stood alone on it
        start = m.start()
        line_start = s.rfind('\n', 0, start) + 1
        if s[line_start:start].strip() == '' and s[end:end + 1] == '\n':
            start, end = line_start, end + 1
        s = s[:start] + s[end:]


def text(fragment):
    return htmllib.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', fragment))).strip()


def faq_jsonld(s):
    qa = []
    for d in re.findall(r'<details\b[^>]*>(.*?)</details>', s, re.S):
        m = re.match(r'\s*<summary>(.*?)</summary>(.*)', d, re.S)
        if m:
            qa.append({'@type': 'Question', 'name': text(m.group(1)),
                       'acceptedAnswer': {'@type': 'Answer', 'text': text(m.group(2))}})
    if not qa:
        return ''
    data = {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': qa}
    return '<script type="application/ld+json">\n%s\n</script>\n' % json.dumps(data, ensure_ascii=False, indent=1)


def build(src, base, default, lang):
    other = [l for l in LANGS if l != lang][0]
    url = {l: base if l == default else base + l + '/' for l in LANGS}
    s = re.sub(r'<html\b[^>]*>', '<html lang="%s" data-lang="%s">' % (lang, lang), src, count=1)
    s = strip_lang(s, other)
    i = LANGS.index(lang)
    s = re.sub(r'\b(alt|aria-label|title)="([^"/]*?) / ([^"/]*?)"',
               lambda m: '%s="%s"' % (m.group(1), (m.group(2), m.group(3))[i]), s)
    if lang != default:  # the page sits one folder deeper
        s = re.sub(r'\b(src|href|poster)="(?!https?:|/|#|mailto:|tel:|data:|\{\{)([^"]+)"', r'\1="../\2"', s)
    s = s.replace('{{url}}', url[lang])
    for l in LANGS:
        s = s.replace('{{url:%s}}' % l, url[l])
    s = s.replace('href="%s"' % url[lang], 'href="%s" aria-current="page"' % url[lang])
    alt = ['<link rel="canonical" href="%s">' % url[lang]]
    alt += ['<link rel="alternate" hreflang="%s" href="%s">' % (l, url[l]) for l in LANGS]
    alt += ['<link rel="alternate" hreflang="x-default" href="%s">' % url[default],
            '<meta property="og:url" content="%s">' % url[lang],
            '<meta property="og:locale" content="%s">' % LOCALE[lang],
            '<meta property="og:locale:alternate" content="%s">' % LOCALE[other]]
    s = s.replace('<!--alternates-->', '\n'.join(alt), 1)
    s = s.replace('</head>', faq_jsonld(s) + '</head>', 1)
    # self-check: nothing of the other language or the template may survive
    assert not re.search(r'<\w+\b[^>]*\blang="%s"' % other, s), 'lang="%s" left in %s page' % (other, lang)
    assert '{{' not in s and '<!--alternates-->' not in s, 'unfilled placeholder in %s page' % lang
    assert s.count('<title') == 1, '%s page needs exactly one <title>' % lang
    return s


def main():
    src_path, out, base, default = sys.argv[1:5]
    assert base.endswith('/') and default in LANGS
    src = open(src_path, encoding='utf-8').read()
    assert '<!--alternates-->' in src, 'source needs <!--alternates--> in <head>'
    for lang in LANGS:
        d = out if lang == default else os.path.join(out, lang)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(build(src, base, default, lang))
        print('%s -> %s' % (lang, os.path.join(d, 'index.html')))


if __name__ == '__main__':
    main()
