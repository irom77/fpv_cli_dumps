import merge_orders as m


def make(vendor, order_number, item, **kw):
    base = {"vendor": vendor, "order_number": order_number, "item": item}
    base.update(kw)
    return m.normalize(base)


def test_columns_order_is_fixed():
    assert m.COLUMNS == [
        "vendor", "order_date", "order_number", "item", "qty",
        "unit_price", "line_total", "category", "build", "flag",
        "source", "notes",
    ]


def test_new_rows_appended_to_existing():
    existing = [make("GetFPV", "1001", "Motor", order_date="2021-02-01")]
    new = [make("RaceDayQuads", "2002", "Props", order_date="2021-03-01")]
    rows, stats = m.merge_orders(existing, new)
    assert stats == {"existing": 1, "added": 1, "updated": 0}
    assert len(rows) == 2
    # sorted by order_date
    assert [r["vendor"] for r in rows] == ["GetFPV", "RaceDayQuads"]


def test_duplicate_key_is_not_duplicated():
    existing = [make("GetFPV", "1001", "Motor", order_date="2021-02-01")]
    new = [make("getfpv", " 1001 ", "  motor ", order_date="2021-02-01")]
    rows, stats = m.merge_orders(existing, new)
    assert stats["added"] == 0
    assert stats["updated"] == 1
    assert len(rows) == 1
