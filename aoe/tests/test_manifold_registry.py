import json

from aoe.manifold import ManifoldRegistry
from aoe.ledger.ledger import ObjectLedger


def test_save_and_reload_atomic(tmp_path):
    registry = ManifoldRegistry(tmp_path)
    player = registry.get_or_create_player("p_test", skill_tier="journeyman")

    mid = player.save_manifold(
        description="test sword",
        composition={"Fe": 99.0, "C": 1.0},
        properties={"density": 7.85, "hardness": 600.0},
    )

    # Persist to disk
    registry.save_player(player)

    # Reload and verify the manifold exists and JSON is valid
    reloaded = registry.get_or_create_player("p_test")
    assert mid in reloaded.manifolds
    # ensure the on-disk file is valid JSON
    p = tmp_path / "p_test.json"
    assert p.exists()
    data = json.loads(p.read_text())
    assert data["player_id"] == "p_test"


def test_ledger_append_on_save(tmp_path):
    ledger = ObjectLedger()
    registry = ManifoldRegistry(tmp_path, ledger=ledger)
    player = registry.get_or_create_player("p_ledger", skill_tier="apprentice")

    mid = player.save_manifold(
        description="oak shield",
        composition={"cellulose": 60.0, "lignin": 28.0, "minerals": 12.0},
        properties={"density": 0.75, "hardness": 3.0},
    )

    registry.save_player(player)

    reloaded = registry.get_or_create_player("p_ledger")
    manifold = reloaded.restore_manifold(mid)
    assert manifold.ledger_tx is not None
    # ledger should contain a transaction with that hash
    assert any(tx["hash"] == manifold.ledger_tx for tx in ledger.history())
