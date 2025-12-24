def assert_schema(obj, schema, path="root"):
    if not isinstance(schema, dict):
        raise AssertionError(f"Schema at {path} must be dict")
    if not isinstance(obj, dict):
        raise AssertionError(f"Object at {path} must be dict")
    for key, spec in schema.items():
        if key not in obj:
            raise AssertionError(f"Missing key {path}.{key}")
        value = obj[key]
        if isinstance(spec, dict):
            assert_schema(value, spec, path=f"{path}.{key}")
        elif isinstance(spec, list):
            if len(spec) != 1:
                raise AssertionError(f"Schema list at {path}.{key} must have 1 item")
            if not isinstance(value, list):
                raise AssertionError(f"Expected list at {path}.{key}")
            for item in value:
                if not isinstance(item, spec[0]):
                    raise AssertionError(f"Invalid item type at {path}.{key}")
        elif isinstance(spec, tuple):
            if not isinstance(value, spec):
                raise AssertionError(f"Invalid type at {path}.{key}")
        else:
            if not isinstance(value, spec):
                raise AssertionError(f"Invalid type at {path}.{key}")
