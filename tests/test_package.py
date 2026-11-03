def test_fin_package_is_importable():
    import fin

    assert fin.__name__ == "fin"
