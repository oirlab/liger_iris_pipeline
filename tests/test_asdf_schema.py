from asdf.schema import load_schema

def test_load_schema():
    uri = "https://oirlab.github.io/schemas/core.schema"
    schema = load_schema(uri)
    assert schema["id"] == uri