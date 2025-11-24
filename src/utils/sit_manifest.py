import json
from jsonschema import validate, ValidationError
from pathlib import Path

SCHEMA_PATH = Path(__file__).parent.parent.parent / 'config' / 'schemas' / 'sit_manifest_schema.json'


def load_schema():
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_manifest(manifest: dict) -> (bool, str):
    schema = load_schema()
    try:
        validate(instance=manifest, schema=schema)
        return True, ''
    except ValidationError as e:
        return False, str(e)
