import json

from psx_ml.runtime.config import RuntimeConfig
from psx_ml.runtime.diagnostics import diagnose
from psx_ml.runtime.metadata import write_manifest


def test_cpu_metadata_schema_and_temporary_output(tmp_path,monkeypatch):
    import psx_ml.runtime.metadata as metadata
    monkeypatch.setattr(metadata.torch.cuda,"is_available",lambda:False)
    result=diagnose(RuntimeConfig(device="cpu"),tmp_path)
    assert set(result) >= {"manifest_version","generated_at_utc","git_commit","python","platform","environment","packages","cuda","selected_device","reproducibility","smoke_test"}
    assert set(result["packages"]) == {"numpy","pyarrow","torch"}
    assert result["cuda"]["available"] is False
    assert result["selected_device"] == "cpu"
    assert result["smoke_test"]["comparison_passed"]
    out=tmp_path/"manifest.json"; write_manifest(result,out)
    assert json.loads(out.read_text())["manifest_version"] == 1
    forbidden=("TOKEN","PASSWORD","SECRET","API_KEY")
    assert not any(any(x in k.upper() for x in forbidden) for k in result)
