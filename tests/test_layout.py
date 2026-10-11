from scan2kindle.layout import (
    clean_toc_title,
    detect_article_openers,
    join_text,
    normalize_text,
    parse_contents,
)
from scan2kindle.models import Line


def line(text, x0, y0, x1=None, h=40):
    return Line(text, 0.99, x0, y0, x1 if x1 is not None else x0 + len(text) * h, y0 + h)


def test_normalize_chinese_punctuation_and_leaders():
    assert normalize_text("你好,世界") == "你好，世界"
    assert normalize_text("标题⋯⋯⋯作者") == "标题……作者"


def test_join_text_keeps_spaces_only_between_latin_words():
    assert join_text("hello", "world") == "hello world"
    assert join_text("中文", "继续") == "中文继续"


def test_clean_toc_title_extracts_author():
    assert clean_toc_title("故宫改建计划始末 王军") == ("故宫改建计划始末", "王军")
    assert clean_toc_title("启蒙年代的歌声……李太山") == ("启蒙年代的歌声", "李太山")


def test_parse_numbered_contents_page():
    contents = [
        line("目录", 300, 100),
        line("1 第一篇文章 作者甲", 200, 300),
        line("35 第二篇文章 作者乙", 200, 380),
        line("80 第三篇文章 作者丙", 200, 460),
    ]
    articles, toc_pages = parse_contents([[], contents])
    assert toc_pages == {1}
    assert [(a.page, a.title, a.author) for a in articles] == [
        (1, "第一篇文章", "作者甲"),
        (35, "第二篇文章", "作者乙"),
        (80, "第三篇文章", "作者丙"),
    ]


def article_page(title, author):
    body = [line("这是一行足够长的正文文字用于判断版面" + str(i), 100, 900 + i * 50, 1200) for i in range(6)]
    return [line(title, 300, 400, h=80), line(author, 360, 520)] + body


def test_detect_article_openers_without_contents_page():
    pages = [[], [], article_page("第一篇", "张三"), [], article_page("第二篇", "李四"), article_page("第三篇", "王五")]
    ocr = [{"width": 1400, "height": 2200} for _ in pages]
    articles = detect_article_openers(pages, ocr, 40)
    assert [(a.start, a.title, a.author) for a in articles] == [(2, "第一篇", "张三"), (4, "第二篇", "李四"), (5, "第三篇", "王五")]
