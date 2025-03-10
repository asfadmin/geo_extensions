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
    split_polygons = list(
        split_polygon_on_antimeridian_ccw(antimeridian_centered_rectangle),
    )
    assert split_polygons == [
        Polygon([
            (179.999, -10),
            (179.999, 10.),
            (150., 10.),
            (150., -10),
            (179.999, -10),
        ]),
        Polygon([
            (-179.999, 10),
            (-179.999, -10.),
            (-150., -10.),
            (-150., 10),
            (-179.999, 10),
        ]),
    ]


def test_split_polygon_on_antimeridian_ccw_crosses_multiple_times(
    multi_crossing_polygon,
):
    split_polygons = list(
        split_polygon_on_antimeridian_ccw(multi_crossing_polygon),
    )
    assert split_polygons == [
        Polygon([
            (179.999, -10),
            (179.999, -4),
            (160, 0),
            (179.999, 4),
            (179.999, 10),
            (150, 10),
            (150, -10),
        ]),
        Polygon([(-179.999, -4), (-179.999, -10), (-150, -10), (-179.999, -4)]),
        Polygon([(-179.999, 10), (-179.999, 4), (-150, 10), (-179.999, 10)]),
    ]


def test_split_polygon_on_antimeridian_ccw_west():
    """Polygon is mostly west of the IDL"""
    polygon = Polygon([
        (170., 70.), (170., 60.), (-179., 60.),
        (-179., 70.), (170., 70.)
    ])
    assert not polygon.exterior.is_ccw

    assert list(split_polygon_on_antimeridian_ccw(polygon)) == [
        Polygon([
            (179.999, 60.),
            (179.999, 70.),
            (170., 70.),
            (170., 60.),
            (179.999, 60.),
        ]),
        Polygon([
            (-179.999, 70.),
            (-179.999, 60.),
            (-179., 60.),
            (-179., 70.),
            (-179.999, 70.),
        ]),
    ]


def test_split_polygon_on_antimeridian_ccw_east():
    """Polygon is mostly east of the IDL"""
    polygon = Polygon([
        (179., 70.), (179., 60.), (-170., 60.),
        (-170., 70.), (179., 70.)
    ])
    assert not polygon.exterior.is_ccw

    assert list(split_polygon_on_antimeridian_ccw(polygon)) == [
        Polygon([
            (179.999, 60.),
            (179.999, 70.),
            (179., 70.),
            (179., 60.),
            (179.999, 60.),
        ]),
        Polygon([
            (-179.999, 70.),
            (-179.999, 60.),
            (-170., 60.),
            (-170., 70.),
            (-179.999, 70.),
        ]),
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
    polygons = split_polygon_on_antimeridian_ccw(polygon)

    # Comparing the polygons directly doesn't seem to work for some reason.
    coords = [list(poly.boundary.coords) for poly in polygons]
    assert coords == [
        [
            (179.999, 49.68139432176656),
            (179.999, 50.21196666666666),
            (179.64800000000002, 50.172),
            (179.79399999999998, 49.658),
            (179.999, 49.68139432176656),
        ],
        [
            (-179.999, 50.21196666666666),
            (-179.999, 49.68139432176656),
            (-179.255, 49.766),
            (-179.392, 50.281),
            (-179.999, 50.21196666666666),
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
    polygons = split_polygon_on_antimeridian_ccw(polygon)

    # Comparing the polygons directly doesn't seem to work for some reason.
    coords = [list(poly.boundary.coords) for poly in polygons]
    assert coords == [
        [
            (-179.999, -76.76296336101612),
            (-179.999, -79.438),
            (-178.328, -79.438),
            (-179.999, -76.76296336101612),
        ],
        [
            (179.999, -79.438),
            (179.999, -76.76296336101612),
            (179.625, -76.163),
            (166.08400000000006, -76.163),
            (164.03700000000003, -79.438),
            (179.999, -79.438),
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
    polygons = split_polygon_on_antimeridian_ccw(polygon)

    # Comparing the polygons directly doesn't seem to work for some reason.
    coords = [list(poly.boundary.coords) for poly in polygons]
    assert coords == [
        [
            (179.999, 66.140),
            (179.999, 66.663),
            (178.83400000000006, 66.663),
            (178.83400000000006, 66.140),
            (179.999, 66.140),
        ],
        [
            (-179.999, 66.663),
            (-179.999, 66.140),
            (-178.918, 66.140),
            (-178.918, 66.663),
            (-179.999, 66.663),
        ],
    ]


def test_split_polygon_on_antimeridian_fixed_size_alos2_example():
    """Example from ALOS2: ALOS2014555550-140830"""
    polygon = Polygon([
        (-164.198, -82.125), (172.437, -83.885), (165.618, -80.869),
        (-176.331, -79.578), (-164.198, -82.125),
    ])
    polygons = split_polygon_on_antimeridian_fixed_size(40)(polygon)

    # Comparing the polygons directly doesn't seem to work for some reason.
    coords = [list(poly.boundary.coords) for poly in polygons]
    assert all(poly.is_ccw for poly in polygons)
    assert coords == [
        [
            (-164.198, -82.125),
            (-176.331, -79.578),
            (-179.999, -79.84040535150407),
            (-179.999, -83.31530686924889),
            (-164.198, -82.125),
        ],
        [
            (179.999, -83.31530686924889),
            (179.999, -79.84040535150407),
            (165.61799999999994, -80.869),
            (172.437, -83.885),
            (179.999, -83.31530686924889),
        ],
    ]
