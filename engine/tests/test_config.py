"""测试全局配置"""

from deepcut.config import DeepCutConfig, get_config


def test_default_config() -> None:
    """默认配置值正确"""
    config = DeepCutConfig()
    assert config.deepcut_default_min_duration == 15.0
    assert config.deepcut_default_max_duration == 60.0
    assert config.deepcut_overlap_duration == 1.5
    assert config.whisper_model == "base"
    assert config.whisper_device == "cpu"
    assert config.deepcut_log_level == "INFO"


def test_get_config_returns_instance() -> None:
    """get_config 返回 DeepCutConfig 实例"""
    config = get_config()
    assert isinstance(config, DeepCutConfig)
