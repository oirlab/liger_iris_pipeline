from asdf.schema import load_schema

def test_load_schema():
    uri = "https://oirlab.github.io/schemas/liger_iris_core.schema"
    schema = load_schema(uri)
    assert schema["id"] == uri