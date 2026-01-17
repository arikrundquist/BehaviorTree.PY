from pathlib import Path
from typing import Final

import pytest
from btpy import BTParser
from btpy.core import BTWriter


@pytest.fixture
def main_xml_file() -> Path:
    return Path(__file__).parent / "main.xml"


def test_parse_from_file(main_xml_file: Path) -> None:
    expected: Final = """
<?xml version="1.0" encoding="UTF-8"?>
<root BTCPP_format="4" main_tree_to_execute="main">
  <BehaviorTree ID="main">
    <Fallback>
      <SubTree ID="helper" name="call_helper" />
      <SubTree ID="helper" name="call_helper_again" />
    </Fallback>
  </BehaviorTree>
  <BehaviorTree ID="helper">
    <Sequence name="helper_called" />
  </BehaviorTree>
</root>
"""
    actual = BTWriter.to_xml(BTParser().parse(main_xml_file), indent=2)
    assert actual.strip() == expected.strip()


def test_parse_from_string(main_xml_file: Path) -> None:
    from_file = BTWriter.to_xml(BTParser().parse(main_xml_file))
    assert from_file == BTWriter.to_xml(BTParser().parse_string(from_file))


def test_ignores_tree_nodes_model() -> None:
    xml = """
<?xml version="1.0" encoding="UTF-8"?>
<root BTCPP_format="4">
    <BehaviorTree ID="main">
        <Sequence />
    </BehaviorTree>

    <TreeNodesModel>
        <!-- this does nothing -->
    </TreeNodesModel>
</root>
""".strip()
    BTParser().parse_string(xml)


def test_errors_on_invalid_tag() -> None:
    xml = """
<?xml version="1.0" encoding="UTF-8"?>
<root BTCPP_format="4">
    <BehaviorTree ID="main">
        <Sequence />
    </BehaviorTree>

    <BadTag />
</root>
""".strip()
    with pytest.raises(RuntimeError):
        BTParser().parse_string(xml)
