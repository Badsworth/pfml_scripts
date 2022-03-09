from typing import Dict, List


def assert_structural_subset(child: Dict, parent: Dict) -> None:
    parent_keys = parent.keys()

    for field, value in child.items():
        assert field in parent_keys

        if isinstance(value, Dict) and isinstance(parent[field], Dict):
            assert_structural_subset(value, parent[field])
        if isinstance(value, List) and len(value) > 0 and isinstance(parent[field], List):
            new_parent = parent[field][0]
            new_child = value[0]
            assert_structural_subset(new_child, new_parent)
