import shapely.geometry
import strategies
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from shapely.geometry import Polygon

from geo_extensions.transformations import (
    drop_z_coordinate,
    split_polygon_on_antimeridian_ccw,
    split_polygon_on_antimeridian_fixed_size,
)


def test_drop_z_coordinate():
    polygon = Polygon([
        (180, 1, 10),
        (180, 0, 10),
        (-179.999, 0, 10),
        (-179.999, 1, 10),
        (180, 1, 10),
    ])
    assert list(drop_z_coordinate(polygon)) == [
        Polygon([
            (180, 1),
            (180, 0),
            (-179.999, 0),
            (-179.999, 1),
            (180, 1),
        ])
    ]


def test_drop_z_coordinate_noop():
    polygon = Polygon([
        (180, 1),
        (180, 0),
        (-179.999, 0),
        (-179.999, 1),
        (180, 1),
    ])
    assert list(drop_z_coordinate(polygon)) == [polygon]


@given(polygon=strategies.rectangles())
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_split_polygon_on_antimeridian_ccw_returns_ccw(polygon):
    for poly in split_polygon_on_antimeridian_ccw(polygon):
        assert poly.exterior.is_ccw
        assert poly.exterior.is_valid


@given(
    polygon=strategies.rectangles(
        # Very small polygons near the antimeridian will be culled.
        lons=st.floats(min_value=-179.990, max_value=180),
    )
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_split_polygon_on_antimeridian_ccw_returns_non_empty_list(polygon):
    assert split_polygon_on_antimeridian_ccw(polygon)


def test_split_polygon_on_antimeridian_ccw_returns_empty_list():
    # There is a case where the input polygon is really small, and both split
    # parts are culled.
    polygon = Polygon([
        (180, 1), (180, 0), (-179.999, 0), (-179.999, 1), (180, 1)
    ])
    assert list(split_polygon_on_antimeridian_ccw(polygon)) == []


def test_split_polygon_on_antimeridian_ccw_noop(rectangle):
    split_polygons = list(split_polygon_on_antimeridian_ccw(rectangle))
    assert split_polygons == [rectangle]


def test_split_polygon_on_antimeridian_ccw_centered_noop(centered_rectangle):
    split_polygons = list(split_polygon_on_antimeridian_ccw(centered_rectangle))
    assert split_polygons == [centered_rectangle]


def test_split_polygon_on_antimeridian_ccw_centered(antimeridian_centered_rectangle):
    """Polygon is centered on IDL"""
    polygons = list(
        split_polygon_on_antimeridian_ccw(antimeridian_centered_rectangle),
    )

    for poly in polygons:
        assert poly.exterior.is_ccw
        assert poly.exterior.is_valid

    assert polygons == [
        Polygon([
            (180., -10),
            (180., 10.),
            (150., 10.),
            (150., -10),
            (180., -10),
        ]),
        Polygon([
            (-180., 10),
            (-180., -10.),
            (-150., -10.),
            (-150., 10),
            (-180., 10),
        ]),
    ]


def test_split_polygon_on_antimeridian_ccw_crosses_multiple_times(
    multi_crossing_polygon,
):
    polygons = list(
        split_polygon_on_antimeridian_ccw(multi_crossing_polygon),
    )

    for poly in polygons:
        assert poly.exterior.is_ccw
        assert poly.exterior.is_valid

    assert polygons == [
        Polygon([
            (180., -10),
            (180., -4),
            (160., 0),
            (180., 4),
            (180., 10),
            (150., 10),
            (150., -10),
        ]),
        Polygon([(-180., -4), (-180., -10), (-150., -10), (-180., -4)]),
        Polygon([(-180., 10), (-180., 4), (-150., 10), (-180., 10)]),
    ]


def test_split_polygon_on_antimeridian_ccw_west():
    """Polygon is mostly west of the IDL"""
    polygon = Polygon([
        (170., 70.), (170., 60.), (-179., 60.),
        (-179., 70.), (170., 70.)
    ])
    assert not polygon.exterior.is_ccw
    polygons = list(split_polygon_on_antimeridian_ccw(polygon))

    for poly in polygons:
        assert poly.exterior.is_ccw
        assert poly.exterior.is_valid

    assert polygons == [
        Polygon([
            (180., 60.),
            (180., 70.),
            (170., 70.),
            (170., 60.),
            (180., 60.),
        ]),
        Polygon([
            (-180., 70.),
            (-180., 60.),
            (-179., 60.),
            (-179., 70.),
            (-180., 70.),
        ]),
    ]


def test_split_polygon_on_antimeridian_ccw_east():
    """Polygon is mostly east of the IDL"""
    polygon = Polygon([
        (179., 70.), (179., 60.), (-170., 60.),
        (-170., 70.), (179., 70.)
    ])
    assert not polygon.exterior.is_ccw
    polygons = list(split_polygon_on_antimeridian_ccw(polygon))

    for poly in polygons:
        assert poly.exterior.is_ccw
        assert poly.exterior.is_valid

    assert polygons == [
        Polygon([
            (180., 60.),
            (180., 70.),
            (179., 70.),
            (179., 60.),
            (180., 60.),
        ]),
        Polygon([
            (-180., 70.),
            (-180., 60.),
            (-170., 60.),
            (-170., 70.),
            (-180., 70.),
        ]),
    ]


def test_split_polygon_on_antimeridian_ccw_close_point():
    """Polygon has a point that is extremely close to the antimeridian"""
    polygon = Polygon([
        (179.999999, 70.),
        (179., 60.), (-170., 60.),
        (-170., 70.), (179., 70.)
    ])
    assert not polygon.exterior.is_ccw
    polygons = list(split_polygon_on_antimeridian_ccw(polygon))

    for poly in polygons:
        assert poly.exterior.is_ccw
        assert poly.exterior.is_valid

    # Comparing the polygons directly doesn't seem to work for some reason.
    coords = [list(poly.boundary.coords) for poly in polygons]
    assert coords == [
        [
            (180., 60.),
            (180., 70.),
            (179.999999, 70.),
            (179., 60.),
            (180., 60.),
        ],
        [
            (-180., 70.),
            (-180., 60.),
            (-170., 60.),
            (-170., 70.),
            (-180., 70.),
        ],
    ]


def test_split_polygon_on_antimeridian_ccw_alos_example():
    """Example from ALOS mission: ALPSRP237090990-L1.1"""
    polygon = Polygon([
        (179.648, 50.172),
        (179.794, 49.658),
        (-179.255, 49.766),
        (-179.392, 50.281),
        (179.648, 50.172),
    ])
    polygons = list(split_polygon_on_antimeridian_ccw(polygon))

    for poly in polygons:
        assert poly.exterior.is_ccw
        assert poly.exterior.is_valid

    # Comparing the polygons directly doesn't seem to work for some reason.
    coords = [list(poly.boundary.coords) for poly in polygons]
    assert coords == [
        [
            (180., 49.68139432176656),
            (180., 50.21196666666666),
            (179.64800000000002, 50.172),
            (179.79399999999998, 49.658),
            (180., 49.68139432176656),
        ],
        [
            (-180., 50.21196666666666),
            (-180., 49.68139432176656),
            (-179.255, 49.766),
            (-179.392, 50.281),
            (-180., 50.21196666666666),
        ],
    ]


def test_split_polygon_on_antimeridian_ccw_alos2_example():
    """ALOS2 granule: ALOS2075945400-151019-WBDR1.1__D"""
    polygon = Polygon([
        (-178.328, -79.438),
        (179.625, -76.163),
        (166.084, -76.163),
        (164.037, -79.438),
    ])
    polygons = list(split_polygon_on_antimeridian_ccw(polygon))

    for poly in polygons:
        assert poly.exterior.is_ccw
        assert poly.exterior.is_valid

    # Comparing the polygons directly doesn't seem to work for some reason.
    coords = [list(poly.boundary.coords) for poly in polygons]
    assert coords == [
        [
            (-180., -76.76296336101612),
            (-180., -79.438),
            (-178.328, -79.438),
            (-180., -76.76296336101612),
        ],
        [
            (180., -79.438),
            (180., -76.76296336101612),
            (179.625, -76.163),
            (166.08400000000006, -76.163),
            (164.03700000000003, -79.438),
            (180., -79.438),
        ],
    ]


def test_split_polygon_on_antimeridian_ccw_opera_example():
    """Example from OPERA RTC Static layer:

    OPERA_L2_RTC-S1-STATIC_T001-000677-IW2_20140403_S1A_30_v1.0
    """
    north, west, south, east = (
        66.663,
        178.834,
        66.140,
        -178.918,
    )
    polygon = shapely.geometry.box(east, north, west, south, ccw=True)
    polygons = list(split_polygon_on_antimeridian_ccw(polygon))

    for poly in polygons:
        assert poly.exterior.is_ccw
        assert poly.exterior.is_valid

    # Comparing the polygons directly doesn't seem to work for some reason.
    coords = [list(poly.boundary.coords) for poly in polygons]
    assert coords == [
        [
            (180., 66.140),
            (180., 66.663),
            (178.83400000000006, 66.663),
            (178.83400000000006, 66.140),
            (180., 66.140),
        ],
        [
            (-180., 66.663),
            (-180., 66.140),
            (-178.918, 66.140),
            (-178.918, 66.663),
            (-180., 66.663),
        ],
    ]


def test_split_polygon_on_antimeridian_ccw_opera_example_pre_split():
    """Example from OPERA CLSC which crosses the IDL but is pre-split:

    OPERA_L2_CSLC-S1_T001-000688-IW1_20250504T183220Z_20250505T112029Z_S1A_VV_v1.1
    """
    polygon = Polygon([
        (180, 64.67712437067621),
        (180, 64.50629047887854),
        (179.9988239237079, 64.50640025835617),
        (179.9167734717595, 64.51400884003007),
        (179.999315144991, 64.6771877237759),
        (180, 64.67712437067621),
    ])
    assert not polygon.exterior.is_ccw
    polygons = list(split_polygon_on_antimeridian_ccw(polygon))

    for poly in polygons:
        assert poly.exterior.is_ccw
        assert poly.exterior.is_valid

    # Comparing the polygons directly doesn't seem to work for some reason.
    coords = [list(poly.boundary.coords) for poly in polygons]
    assert coords == [
        [
            (180.0, 64.67712437067621),
            (179.999315144991, 64.6771877237759),
            (179.91677347175948, 64.51400884003007),
            (179.99882392370796, 64.50640025835617),
            (180.0, 64.50629047887854),
            (180.0, 64.67712437067621),
        ],
    ]


def test_split_polygon_on_antimeridian_fixed_size_alos2_example():
    """Example from ALOS2: ALOS2014555550-140830"""
    polygon = Polygon([
        (-164.198, -82.125), (172.437, -83.885), (165.618, -80.869),
        (-176.331, -79.578), (-164.198, -82.125),
    ])
    polygons = list(split_polygon_on_antimeridian_fixed_size(40)(polygon))

    for poly in polygons:
        assert poly.exterior.is_ccw
        assert poly.exterior.is_valid

    # Comparing the polygons directly doesn't seem to work for some reason.
    coords = [list(poly.boundary.coords) for poly in polygons]
    assert coords == [
        [
            (-164.198, -82.125),
            (-176.331, -79.578),
            (-180., -79.84040535150407),
            (-180., -83.31530686924889),
            (-164.198, -82.125),
        ],
        [
            (180., -83.31530686924889),
            (180., -79.84040535150407),
            (165.61799999999994, -80.869),
            (172.437, -83.885),
            (180., -83.31530686924889),
        ],
    ]
