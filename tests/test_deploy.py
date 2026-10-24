from scripts.deploy_hf import deployment_files


def test_deploy_excludes_secrets_and_uploads(tmp_path):
    (tmp_path / "app.py").write_text("pass")
    (tmp_path / ".env").write_text("TOKEN=secret")
    (tmp_path / ".streamlit").mkdir()
    (tmp_path / ".streamlit/secrets.toml").write_text('token="secret"')
    (tmp_path / ".streamlit/config.toml").write_text("")
    (tmp_path / "local_data").mkdir()
    (tmp_path / "local_data/private.json").write_text("{}")
    result = [str(p.relative_to(tmp_path)) for p in deployment_files(tmp_path)]
    assert "app.py" in result and ".streamlit/config.toml" in result
    assert ".env" not in result and ".streamlit/secrets.toml" not in result
    assert "local_data/private.json" not in result
