import re
from html.parser import HTMLParser
from pathlib import Path

import pytest

PUBLIC_DIR = Path(__file__).resolve().parents[2] / "src" / "public"
HTML = (PUBLIC_DIR / "index.html").read_text(encoding="utf-8")
JS = (PUBLIC_DIR / "main.js").read_text(encoding="utf-8")

SECTIONS = {"overview", "cells", "analytics", "alerts", "service", "project"}
VOID_TAGS = {"meta", "link", "img", "br", "input", "hr"}


class Node:
    def __init__(self, tag: str, attrs: dict[str, str], parent: "Node | None") -> None:
        self.tag = tag
        self.attrs = attrs
        self.parent = parent
        self.children: list[Node] = []

    @property
    def classes(self) -> set[str]:
        return set(self.attrs.get("class", "").split())

    def walk(self) -> list["Node"]:
        nodes = [self]
        for child in self.children:
            nodes.extend(child.walk())
        return nodes

    def ancestors(self) -> list["Node"]:
        node, chain = self.parent, []
        while node is not None:
            chain.append(node)
            node = node.parent
        return chain


class TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.root = Node("document", {}, None)
        self.current = self.root

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = Node(tag, {key: value or "" for key, value in attrs}, self.current)
        self.current.children.append(node)
        if tag not in VOID_TAGS:
            self.current = node

    def handle_endtag(self, tag: str) -> None:
        node: Node | None = self.current
        while node is not None and node.tag != tag:
            node = node.parent
        if node is not None and node.parent is not None:
            self.current = node.parent


@pytest.fixture(scope="module")
def nodes() -> list[Node]:
    builder = TreeBuilder()
    builder.feed(HTML)
    return builder.root.walk()


def by_id(nodes: list[Node], element_id: str) -> Node:
    matches = [node for node in nodes if node.attrs.get("id") == element_id]
    assert matches, f"falta #{element_id}"
    return matches[0]


def hidden_on_mobile(node: Node) -> bool:
    return any(
        "hidden" in n.classes and "md:hidden" not in n.classes for n in [node, *node.ancestors()]
    )


def test_zoom_is_not_disabled() -> None:
    viewport = re.search(r'<meta name="viewport" content="([^"]+)"', HTML)

    assert viewport is not None
    assert "width=device-width" in viewport.group(1)
    assert "user-scalable=no" not in viewport.group(1)
    assert "maximum-scale" not in viewport.group(1)


def test_desktop_sidebar_is_not_rendered_on_phones(nodes: list[Node]) -> None:
    sidebar = by_id(nodes, "sidebar")

    assert {"hidden", "md:flex"} <= sidebar.classes
    assert "toggleSidebar" not in HTML
    assert "toggleSidebar" not in JS


def test_bottom_navigation_is_only_for_phones(nodes: list[Node]) -> None:
    nav = by_id(nodes, "mobile-nav")

    assert {"md:hidden", "fixed", "bottom-0"} <= nav.classes
    tabs = [n.attrs["data-tab"] for n in nav.walk() if "data-tab" in n.attrs]
    assert tabs == ["overview", "cells", "analytics", "alerts"]


def test_content_is_not_covered_by_the_bottom_navigation(nodes: list[Node]) -> None:
    main = next(node for node in nodes if node.tag == "main")

    assert {"pb-24", "md:pb-6"} <= main.classes


def test_options_sheet_opens_from_the_mobile_header(nodes: list[Node]) -> None:
    header = next(node for node in nodes if node.tag == "header")
    openers = [n for n in header.walk() if "openMobileSheet" in n.attrs.get("onclick", "")]

    assert openers and "md:hidden" in openers[0].classes
    sheet = by_id(nodes, "mobile-sheet")
    assert "md:hidden" in sheet.classes
    assert {"/docs", "/redoc"} <= {n.attrs.get("href") for n in sheet.walk()}


def test_every_section_is_reachable_on_a_phone(nodes: list[Node]) -> None:
    reachable = {
        n.attrs["data-tab"]
        for container in ("mobile-nav", "mobile-sheet")
        for n in by_id(nodes, container).walk()
        if "data-tab" in n.attrs
    }
    sections = {
        n.attrs["id"].removeprefix("tab-")
        for n in nodes
        if n.attrs.get("id", "").startswith("tab-")
    }

    assert sections == SECTIONS
    assert reachable == SECTIONS


@pytest.mark.parametrize(
    ("mobile_list", "desktop_table"),
    [("alerts-feed", "alerts-table-body"), ("summary-cards", "summary-table-body")],
)
def test_wide_tables_become_card_lists_on_phones(
    nodes: list[Node], mobile_list: str, desktop_table: str
) -> None:
    cards = by_id(nodes, mobile_list)
    table = by_id(nodes, desktop_table)

    assert "md:hidden" in cards.classes or any("md:hidden" in a.classes for a in cards.ancestors())
    assert hidden_on_mobile(table)
    assert f"$('{mobile_list}')" in JS


def test_cell_detail_opens_as_a_bottom_sheet_on_phones(nodes: list[Node]) -> None:
    modal = by_id(nodes, "cell-modal")
    dialog = next(n for n in modal.walk() if n.attrs.get("role") == "dialog")

    assert {"items-end", "md:items-center"} <= modal.classes
    assert any(cls.startswith("rounded-t-") for cls in dialog.classes)


def test_mobile_badges_are_updated_with_the_data() -> None:
    for element_id in ("mobile-cell-count", "mobile-alert-count", "mobile-status-text"):
        assert f"$('{element_id}')" in JS
