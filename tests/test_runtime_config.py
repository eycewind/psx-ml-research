import pytest

from psx_ml.runtime.config import RuntimeConfigurationError, load_runtime_config


def test_runtime_config_loads(tmp_path):
    p=tmp_path/"runtime.toml"; p.write_text('[runtime]\ndevice="cpu"\nseed=7\ndeterministic=true\nallow_tf32=false\n')
    c=load_runtime_config(p)
    assert (c.device,c.seed,c.deterministic,c.allow_tf32)==("cpu",7,True,False)


@pytest.mark.parametrize("text",['[runtime]\ndevice="gpu"','[runtime]\nseed=-1','[runtime]\nsecret="x"'])
def test_invalid_runtime_config_rejected(tmp_path,text):
    p=tmp_path/"bad.toml"; p.write_text(text)
    with pytest.raises(RuntimeConfigurationError): load_runtime_config(p)
