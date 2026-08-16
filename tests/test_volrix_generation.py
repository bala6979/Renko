from pathlib import Path
from datetime import datetime

from renko_research.bricks import RenkoBuilder
from renko_research.config import load_config
from renko_research.volrix import render_volrix_strategy


ROOT = Path(__file__).resolve().parents[1]


def test_generated_volrix_code_is_standalone_and_compiles() -> None:
    config = load_config(ROOT / "configs" / "nifty.yaml")
    code = render_volrix_strategy(config, class_name="NiftyRenkoSample")
    assert "class NiftyRenkoSample(Strategy):" in code
    assert "import " not in code
    assert "__UNDERLYING__" not in code
    assert "while " not in code
    compile(code, "nifty_renko_sample.py", "exec")


def test_banknifty_generator_uses_monthly_contracts() -> None:
    config = load_config(ROOT / "configs" / "banknifty.yaml")
    code = render_volrix_strategy(config, class_name="BankNiftyRenkoSample")
    assert "EXPIRY = 'monthly'" in code
    assert "UNDERLYING = 'BANKNIFTY'" in code


def test_generated_and_local_multi_brick_sequences_match() -> None:
    config = load_config(ROOT / "configs" / "samples" / "banknifty_fixed_reversal.yaml")
    code = render_volrix_strategy(config, class_name="BankNiftyRenkoParity")
    namespace = {"Strategy": object}
    exec(code, namespace)
    remote = namespace["BankNiftyRenkoParity"]()
    remote.init()
    state = remote._new_chart()
    state["last_close"] = 1000.0
    remote_bricks, previous = remote._make_bricks(
        state,
        {"close": 1250.0},
        100.0,
    )

    local = RenkoBuilder(100, initial_price=1000, reversal_bricks=2)
    local_bricks = local.update(datetime(2026, 8, 14, 9, 20), 1250)
    assert previous == 0
    assert [item["close"] for item in remote_bricks] == [
        float(item.close) for item in local_bricks
    ]


def test_committed_samples_are_generator_outputs() -> None:
    cases = [
        ("configs/nifty.yaml", "strategies/volrix/generated_nifty_sample.py", "NiftyRenkoSample"),
        (
            "configs/banknifty.yaml",
            "strategies/volrix/generated_banknifty_sample.py",
            "BankNiftyRenkoSample",
        ),
        (
            "configs/samples/banknifty_fixed_reversal.yaml",
            "strategies/volrix/generated_banknifty_fixed_sample.py",
            "BankNiftyRenkoFixedSample",
        ),
    ]
    for config_path, output_path, class_name in cases:
        expected = render_volrix_strategy(load_config(ROOT / config_path), class_name=class_name)
        assert (ROOT / output_path).read_text(encoding="utf-8") == expected


def test_analysis_generation_records_points_without_option_orders() -> None:
    code = render_volrix_strategy(
        load_config(ROOT / "configs/validation/nifty_30m_sphspl_fixed15.yaml"),
        class_name="NiftyRenkoAnalysis",
        analysis_only=True,
    )
    assert "ANALYSIS_ONLY = True" in code
    assert 'tag="SPH"' in code
    assert 'tag="SPL"' in code
