import pytest
from shapely.errors import ShapelyError
from shapely.geometry import Polygon

from geo_extensions.transformations import simplify_polygon
from geo_extensions.transformer import Transformer


@pytest.fixture
def simplify_transformer():
    return Transformer([
        simplify_polygon(0.1),
    ])


def test_from_wkt(simplify_transformer):
    # Clockwise polygon remains clockwise
    assert simplify_transformer.from_wkt(
        "POLYGON ((50 20, 50 21, 51 21, 51 20, 50 20))",
    ) == [
        Polygon([
            (50.0, 20.0),
            (50.0, 21.0),
            (51.0, 21.0),
            (51.0, 20.0),
            (50.0, 20.0),
        ])
    ]
    assert simplify_transformer.from_wkt(
        "POLYGON(( 1 1, 2 1, 1 2, 1 1))",
    ) == [
        Polygon([
            (1, 1),
            (2, 1),
            (1, 2),
            (1, 1),
        ])
    ]
    # Duplicate point is removed
    assert simplify_transformer.from_wkt(
        "POLYGON ((50 20, 50 21, 51 21, 51 20, 50 20, 50 20))",
    ) == [
        Polygon([
            (50.0, 20.0),
            (50.0, 21.0),
            (51.0, 21.0),
            (51.0, 20.0),
            (50.0, 20.0),
        ])
    ]


def test_from_wkt_multipolygon(simplify_transformer):
    assert simplify_transformer.from_wkt(
        "MULTIPOLYGON (((30 20, 45 40, 10 40, 30 20)),"
        "((15 5, 40 10, 10 20, 5 10, 15 5)))"
    ) == [
        Polygon([
            (30.0, 20.0),
            (45.0, 40.0),
            (10.0, 40.0),
            (30.0, 20.0),
        ]),
        Polygon([
            (15.0, 5.0),
            (40.0, 10.0),
            (10.0, 20.0),
            (5.0, 10.0),
            (15.0, 5.0),
        ]),
    ]


def test_from_geo_json(simplify_transformer):
    # Clockwise polygon remains clockwise
    assert simplify_transformer.from_geo_json({
        "type": "Polygon",
        "coordinates": [
            [
                [50, 20],
                [50, 21],
                [51, 21],
                [51, 20],
                [50, 20],
            ],
        ],
    }) == [
        Polygon([
            (50.0, 20.0),
            (50.0, 21.0),
            (51.0, 21.0),
            (51.0, 20.0),
            (50.0, 20.0),
        ]),
    ]
    assert simplify_transformer.from_geo_json({
        "type": "Polygon",
        "coordinates": [
            [
                [1, 1],
                [2, 1],
                [1, 2],
                [1, 1],
            ],
        ],
    }) == [
        Polygon([
            (1, 1),
            (2, 1),
            (1, 2),
            (1, 1),
        ]),
    ]
    # Duplicate point is removed
    assert simplify_transformer.from_geo_json({
        "type": "Polygon",
        "coordinates": [
            [
                [50.0, 20.0],
                [50.0, 21.0],
                [51.0, 21.0],
                [51.0, 20.0],
                [50.0, 20.0],
                [50.0, 20.0],
            ],
        ],
    }) == [
        Polygon(
            [
                (50.0, 20.0),
                (50.0, 21.0),
                (51.0, 21.0),
                (51.0, 20.0),
                (50.0, 20.0),
            ],
        ),
    ]


def test_from_geo_json_multipolygon(simplify_transformer):
    assert simplify_transformer.from_geo_json(
        {
            "type": "MultiPolygon",
            "coordinates": [
                [
                    [
                        [30, 20],
                        [45, 40],
                        [10, 40],
                        [30, 20],
                    ],
                ],
                [
                    [
                        [15, 5],
                        [40, 10],
                        [10, 20],
                        [5, 10],
                        [15, 5],
                    ],
                ],
            ],
        },
    ) == [
        Polygon(
            [
                (30.0, 20.0),
                (45.0, 40.0),
                (10.0, 40.0),
                (30.0, 20.0),
            ],
        ),
        Polygon(
            [
                (15.0, 5.0),
                (40.0, 10.0),
                (10.0, 20.0),
                (5.0, 10.0),
                (15.0, 5.0),
            ],
        ),
    ]


def test_from_wkt_bad_points(simplify_transformer):
    with pytest.raises(
        Exception,
        match=r"'POINT \(30 10\)' is not a Polygon or MultiPolygon",
    ):
        simplify_transformer.from_wkt("POINT (30 10)")

    with pytest.raises(ShapelyError):
        simplify_transformer.from_wkt("")


def test_from_geo_json_bad_points(simplify_transformer):
    with pytest.raises(
        Exception,
        match=r"'POINT \(30 10\)' is not a Polygon or MultiPolygon",
    ):
        simplify_transformer.from_geo_json({
            "type": "Point",
            "coordinates": [[30, 10]],
        })

    with pytest.raises(AttributeError):
        simplify_transformer.from_geo_json({})
