import pytest
import shapely.geometry
import strategies
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from shapely.geometry import Polygon

from geo_extensions.transformations import (
    densify_polygon,
    drop_z_coordinate,
    round_points,
    simplify_polygon,
    split_polygon_on_antimeridian_ccw,
    split_polygon_on_antimeridian_fixed_size,
)
from geo_extensions.transformations.cartesian import _shift_polygon


def test_simplify():
    polygon = Polygon(
        [
            (20, 0),
            (20, 0),
            (20, 10),
            (0, 10),
            (0, 0),
            (20, 0),
        ]
    )
    assert list(simplify_polygon(0.01)(polygon)) == [
        Polygon(
            [
                (20, 0),
                (20, 10),
                (0, 10),
                (0, 0),
                (20, 0),
            ]
        ),
    ]


def test_simplify_line():
    polygon = Polygon(
        [
            (20, 0),
            (20, 10),
            (20, 10),
            (20, 0),
            (20, 0),
        ]
    )
    assert list(simplify_polygon(0.01)(polygon)) == [
        Polygon(
            [
                (20, 0),
                (20, 10),
                (20, 10),
                (20, 0),
            ]
        ),
    ]

    assert list(simplify_polygon(0.01, preserve_topology=False)(polygon)) == [
        Polygon([]),
    ]


def test_densify():
    polygon = Polygon(
        [
            (50, 75),
            (10, 80),
            (0, 77),
            (40, 70),
            (50, 75),
        ]
    )

    assert list(densify_polygon(50_000)(polygon)) == [
        Polygon(
            [
                (50, 75),
                (34.100003241169595, 78.2028289318241),
                (10, 80),
                (0, 77),
                (24.297878219303588, 74.40374356383884),
                (40, 70),
                (50, 75),
            ]
        ),
    ]


def test_densify_with_holes():
    polygon = Polygon(
        shell=[
            (50, 70),
            (50, 80),
            (0, 80),
            (0, 70),
            (50, 70),
        ],
        holes=[
            [
                (45, 72),
                (45, 78),
                (5, 78),
                (5, 72),
                (45, 72),
            ],
        ],
    )

    assert list(densify_polygon(50_000)(polygon)) == [
        Polygon(
            shell=[
                (50, 70),
                (50, 80),
                (24.999999999999996, 80.92053252671789),
                (0, 80),
                (0, 70),
                (25, 71.7438759890997),
                (50, 70),
            ],
            holes=[
                [
                    (45, 72),
                    (45, 78),
                    (25, 78.70451161084236),
                    (5, 78),
                    (5, 72),
                    (25, 73.02127815507072),
                    (45, 72),
                ],
            ],
        ),
    ]


def test_densify_idempotent():
    polygon = Polygon(
        [
            (50, 75),
            (10, 80),
            (0, 77),
            (40, 70),
            (50, 75),
        ]
    )

    transformation = densify_polygon(50_000)

    densified_polygons = list(transformation(polygon))
    double_densified_polygons = [
        # ruff hint
        poly
        for densified_polygon in densified_polygons
        for poly in transformation(densified_polygon)
    ]

    assert densified_polygons == double_densified_polygons


def test_densify_incomplete():
    assert list(densify_polygon(50_000)(Polygon())) == [Polygon()]


def test_densify_error():
    with pytest.raises(ValueError, match="must be greater than 0"):
        densify_polygon(0)


def test_drop_z_coordinate():
    polygon = Polygon(
        [
            (180, 1, 10),
            (180, 0, 10),
            (-179.999, 0, 10),
            (-179.999, 1, 10),
            (180, 1, 10),
        ]
    )
    assert list(drop_z_coordinate(polygon)) == [
        Polygon(
            [
                (180, 1),
                (180, 0),
                (-179.999, 0),
                (-179.999, 1),
                (180, 1),
            ]
        ),
    ]


def test_drop_z_coordinate_noop():
    polygon = Polygon(
        [
            (180, 1),
            (180, 0),
            (-179.999, 0),
            (-179.999, 1),
            (180, 1),
        ]
    )
    assert list(drop_z_coordinate(polygon)) == [polygon]


def test_drop_z_coordinate_holes():
    polygon = Polygon(
        shell=[
            (100, 10, 10),
            (100, 0, 10),
            (80, 0, 10),
            (80, 10, 10),
            (100, 10, 10),
        ],
        holes=[
            [(93, 8, 10), (83, 8, 10), (83, 2, 10), (93, 8, 10)],
            [(97, 2, 10), (97, 8, 10), (87, 2, 10), (97, 2, 10)],
        ],
    )
    assert list(drop_z_coordinate(polygon)) == [
        Polygon(
            shell=[
                (100, 10),
                (100, 0),
                (80, 0),
                (80, 10),
                (100, 10),
            ],
            holes=[
                [(93, 8), (83, 8), (83, 2), (93, 8)],
                [(97, 2), (97, 8), (87, 2), (97, 2)],
            ],
        ),
    ]


def test_round_polygon_points():
    polygon = Polygon(
        shell=[
            (20.123456789, 0.123456789),
            (20.123456789, 10.123456789),
            (20.123456789, 10.123456789),
            (20.123456789, 0.123456789),
            (20.123456789, 0.123456789),
        ],
        holes=[
            [
                (18.123456789, 2.123456789),
                (18.123456789, 8.123456789),
                (18.123456789, 8.123456789),
                (18.123456789, 2.123456789),
            ],
        ],
    )
    assert list(round_points(3)(polygon)) == [
        Polygon(
            shell=[
                (20.123, 0.123),
                (20.123, 10.123),
                (20.123, 10.123),
                (20.123, 0.123),
                (20.123, 0.123),
            ],
            holes=[
                [
                    (18.123, 2.123),
                    (18.123, 8.123),
                    (18.123, 8.123),
                    (18.123, 2.123),
                ],
            ],
        ),
    ]


def test_shift_polygon_empty():
    assert _shift_polygon(Polygon([])) == Polygon([])


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
    ),
)
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_split_polygon_on_antimeridian_ccw_returns_non_empty_list(polygon):
    assert split_polygon_on_antimeridian_ccw(polygon)


def test_split_polygon_on_antimeridian_ccw_empty():
    assert list(split_polygon_on_antimeridian_ccw(Polygon())) == [Polygon()]


def test_split_polygon_on_antimeridian_fixed_size_empty():
    assert list(split_polygon_on_antimeridian_fixed_size(0)(Polygon())) == [Polygon()]


def test_split_polygon_on_antimeridian_ccw_returns_empty_list():
    # There is a case where the input polygon is really small, and both split
    # parts are culled.
    polygon = Polygon(
        [
            (180, 1),
            (180, 0),
            (-179.999, 0),
            (-179.999, 1),
            (180, 1),
        ]
    )
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
        Polygon(
            [
                (180.0, -10),
                (180.0, 10.0),
                (150.0, 10.0),
                (150.0, -10),
                (180.0, -10),
            ]
        ),
        Polygon(
            [
                (-180.0, 10),
                (-180.0, -10.0),
                (-150.0, -10.0),
                (-150.0, 10),
                (-180.0, 10),
            ]
        ),
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
        Polygon(
            [
                (180.0, -10),
                (180.0, -4),
                (160.0, 0),
                (180.0, 4),
                (180.0, 10),
                (150.0, 10),
                (150.0, -10),
            ]
        ),
        Polygon([(-180.0, -4), (-180.0, -10), (-150.0, -10), (-180.0, -4)]),
        Polygon([(-180.0, 10), (-180.0, 4), (-150.0, 10), (-180.0, 10)]),
    ]


def test_split_polygon_on_antimeridian_ccw_west():
    """Polygon is mostly west of the IDL"""
    polygon = Polygon(
        [
            (170.0, 70.0),
            (170.0, 60.0),
            (-179.0, 60.0),
            (-179.0, 70.0),
            (170.0, 70.0),
        ]
    )
    assert not polygon.exterior.is_ccw
    polygons = list(split_polygon_on_antimeridian_ccw(polygon))

    for poly in polygons:
        assert poly.exterior.is_ccw
        assert poly.exterior.is_valid

    assert polygons == [
        Polygon(
            [
                (180.0, 60.0),
                (180.0, 70.0),
                (170.0, 70.0),
                (170.0, 60.0),
                (180.0, 60.0),
            ]
        ),
        Polygon(
            [
                (-180.0, 70.0),
                (-180.0, 60.0),
                (-179.0, 60.0),
                (-179.0, 70.0),
                (-180.0, 70.0),
            ]
        ),
    ]


def test_split_polygon_on_antimeridian_ccw_east():
    """Polygon is mostly east of the IDL"""
    polygon = Polygon(
        [
            (179.0, 70.0),
            (179.0, 60.0),
            (-170.0, 60.0),
            (-170.0, 70.0),
            (179.0, 70.0),
        ]
    )
    assert not polygon.exterior.is_ccw
    polygons = list(split_polygon_on_antimeridian_ccw(polygon))

    for poly in polygons:
        assert poly.exterior.is_ccw
        assert poly.exterior.is_valid

    assert polygons == [
        Polygon(
            [
                (180.0, 60.0),
                (180.0, 70.0),
                (179.0, 70.0),
                (179.0, 60.0),
                (180.0, 60.0),
            ]
        ),
        Polygon(
            [
                (-180.0, 70.0),
                (-180.0, 60.0),
                (-170.0, 60.0),
                (-170.0, 70.0),
                (-180.0, 70.0),
            ]
        ),
    ]


def test_split_polygon_on_antimeridian_ccw_close_point():
    """Polygon has a point that is extremely close to the antimeridian"""
    polygon = Polygon(
        [
            (179.999999, 70.0),
            (179.0, 60.0),
            (-170.0, 60.0),
            (-170.0, 70.0),
            (179.0, 70.0),
        ]
    )
    assert not polygon.exterior.is_ccw
    polygons = list(split_polygon_on_antimeridian_ccw(polygon))

    for poly in polygons:
        assert poly.exterior.is_ccw
        assert poly.exterior.is_valid

    # Comparing the polygons directly doesn't seem to work for some reason.
    coords = [list(poly.boundary.coords) for poly in polygons]
    assert coords == [
        [
            (180.0, 60.0),
            (180.0, 70.0),
            (179.999999, 70.0),
            (179.0, 60.0),
            (180.0, 60.0),
        ],
        [
            (-180.0, 70.0),
            (-180.0, 60.0),
            (-170.0, 60.0),
            (-170.0, 70.0),
            (-180.0, 70.0),
        ],
    ]


def test_split_polygon_on_antimeridian_ccw_alos_example():
    """Example from ALOS mission: ALPSRP237090990-L1.1"""
    polygon = Polygon(
        [
            (179.648, 50.172),
            (179.794, 49.658),
            (-179.255, 49.766),
            (-179.392, 50.281),
            (179.648, 50.172),
        ]
    )
    polygons = list(split_polygon_on_antimeridian_ccw(polygon))

    for poly in polygons:
        assert poly.exterior.is_ccw
        assert poly.exterior.is_valid

    # Comparing the polygons directly doesn't seem to work for some reason.
    coords = [list(poly.boundary.coords) for poly in polygons]
    assert coords == [
        [
            (180.0, 49.68139432176656),
            (180.0, 50.21196666666666),
            (179.648, 50.172),
            (179.794, 49.658),
            (180.0, 49.68139432176656),
        ],
        [
            (-180.0, 50.21196666666666),
            (-180.0, 49.68139432176656),
            (-179.255, 49.766),
            (-179.392, 50.281),
            (-180.0, 50.21196666666666),
        ],
    ]


def test_split_polygon_on_antimeridian_ccw_alos2_example():
    """ALOS2 granule: ALOS2075945400-151019-WBDR1.1__D"""
    polygon = Polygon(
        [
            (-178.328, -79.438),
            (179.625, -76.163),
            (166.084, -76.163),
            (164.037, -79.438),
        ]
    )
    polygons = list(split_polygon_on_antimeridian_ccw(polygon))

    for poly in polygons:
        assert poly.exterior.is_ccw
        assert poly.exterior.is_valid

    # Comparing the polygons directly doesn't seem to work for some reason.
    coords = [list(poly.boundary.coords) for poly in polygons]
    assert coords == [
        [
            (-180.0, -76.76296336101612),
            (-180.0, -79.438),
            (-178.328, -79.438),
            (-180.0, -76.76296336101612),
        ],
        [
            (180.0, -79.438),
            (180.0, -76.76296336101612),
            (179.625, -76.163),
            (166.084, -76.163),
            (164.037, -79.438),
            (180.0, -79.438),
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
            (180.0, 66.140),
            (180.0, 66.663),
            (178.834, 66.663),
            (178.834, 66.140),
            (180.0, 66.140),
        ],
        [
            (-180.0, 66.663),
            (-180.0, 66.140),
            (-178.918, 66.140),
            (-178.918, 66.663),
            (-180.0, 66.663),
        ],
    ]


def test_split_polygon_on_antimeridian_ccw_opera_example_pre_split():
    """Example from OPERA CLSC which crosses the IDL but is pre-split:

    OPERA_L2_CSLC-S1_T001-000688-IW1_20250504T183220Z_20250505T112029Z_S1A_VV_v1.1
    """
    polygon = Polygon(
        [
            (180, 64.67712437067621),
            (180, 64.50629047887854),
            (179.9988239237079, 64.50640025835617),
            (179.9167734717595, 64.51400884003007),
            (179.999315144991, 64.6771877237759),
            (180, 64.67712437067621),
        ]
    )
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
            (179.9167734717595, 64.51400884003007),
            (179.9988239237079, 64.50640025835617),
            (180.0, 64.50629047887854),
            (180.0, 64.67712437067621),
        ],
    ]


def test_split_polygon_on_antimeridian_ccw_sentinel_ocn_example():
    """Sentinel-1 granule: S1A_WV_OCN__2SSV_20250417T170934_20250417T172302_058799_07490A_662C"""
    polygon = Polygon(
        [
            (-173.31352985574108, -23.14698567224461),
            (-173.77162229214494, -24.907619019866505),
            (-174.2415526063507, -26.665847671745183),
            (-174.735358150903, -28.420448333916106),
            (-175.23380277184344, -30.175206972263744),
            (-175.74843654546004, -31.927869767925337),
            (-176.2807594129271, -33.67798464336149),
            (-176.84487055921355, -35.423184310947256),
            (-177.41910677624742, -37.16801395691638),
            (-178.0174237891529, -38.90994274849644),
            (-178.6424368542418, -40.64852489269256),
            (-179.29727678081028, -42.38361736393),
            (-179.99919575326913, -44.11165778890455),
            (179.27499973531806, -45.83867913785123),
            (178.50719394616408, -47.561023088516535),
            (177.69231780926836, -49.27817128078806),
            (176.80904931895057, -50.986415957829536),
            (175.87985821681252, -52.69120887337212),
            (174.8814954194563, -54.38819050545594),
            (173.80356416208477, -56.07742986626234),
            (172.6342022987177, -57.75707684914518),
            (171.3430337906186, -59.42214751260288),
            (169.94378551545861, -61.077752113025916),
            (168.3999709466183, -62.71805533391731),
            (166.6843566389666, -64.34111371291355),
            (164.74985524368935, -65.9397497607168),
            (162.5883735575569, -67.5152692747083),
            (160.1325459675333, -69.06048810117184),
            (154.88126113623596, -68.86722808467104),
            (157.66232733899088, -67.40109715863518),
            (160.11788634153672, -65.89157783252615),
            (162.30350978708452, -64.34830642665239),
            (164.26115705334965, -62.776359315577984),
            (166.0243795283944, -61.18062028554268),
            (167.62930602018182, -59.5668614442984),
            (169.08373088867933, -57.93420475768521),
            (170.41560899457167, -56.28647419580335),
            (171.64130903910598, -54.625361215229724),
            (172.78119311087207, -52.95574121072587),
            (173.83243861741815, -51.273905612708624),
            (174.81205988512076, -49.58367135376619),
            (175.72884840278266, -47.885484758555855),
            (176.58940809511245, -46.18095578091026),
            (177.407673659417, -44.471546605796334),
            (178.17413248284223, -42.75510333566816),
            (178.90089160626385, -41.03375212942789),
            (179.59202341272197, -39.307739657248156),
            (-179.74246296618378, -37.57885571562622),
            (-179.11269276255436, -35.84470103625437),
            (-178.50911206250385, -34.10700088461006),
            (-177.92939864490123, -32.366184612752285),
            (-177.3711810617254, -30.622149243259848),
            (-176.8274107386524, -28.87700042708585),
            (-176.30710772502422, -27.127570832268837),
            (-175.8034798185683, -25.37659855071509),
            (-175.3146666830624, -23.622777737104464),
            (-173.31352985574108, -23.14698567224461),
        ]
    )
    polygons = list(split_polygon_on_antimeridian_ccw(polygon))

    for poly in polygons:
        assert poly.exterior.is_ccw
        assert poly.exterior.is_valid

    # Comparing the polygons directly doesn't seem to work for some reason.
    coords = [list(poly.boundary.coords) for poly in polygons]
    assert coords == [
        [
            (-173.31352985574108, -23.14698567224461),
            (-175.3146666830624, -23.622777737104464),
            (-175.8034798185683, -25.37659855071509),
            (-176.30710772502422, -27.127570832268837),
            (-176.8274107386524, -28.87700042708585),
            (-177.3711810617254, -30.622149243259848),
            (-177.92939864490123, -32.366184612752285),
            (-178.50911206250385, -34.10700088461006),
            (-179.11269276255436, -35.84470103625437),
            (-179.74246296618378, -37.57885571562622),
            (-180.0, -38.247890319915335),
            (-180.0, -44.11357146021988),
            (-179.99919575326913, -44.11165778890455),
            (-179.29727678081028, -42.38361736393),
            (-178.6424368542418, -40.64852489269256),
            (-178.0174237891529, -38.90994274849644),
            (-177.41910677624742, -37.16801395691638),
            (-176.84487055921355, -35.423184310947256),
            (-176.2807594129271, -33.67798464336149),
            (-175.74843654546004, -31.927869767925337),
            (-175.23380277184344, -30.175206972263744),
            (-174.735358150903, -28.420448333916106),
            (-174.2415526063507, -26.665847671745183),
            (-173.77162229214494, -24.907619019866505),
            (-173.31352985574108, -23.14698567224461),
        ],
        [
            (180.0, -44.11357146021988),
            (180.0, -38.247890319915335),
            (179.59202341272197, -39.307739657248156),
            (178.90089160626385, -41.03375212942789),
            (178.17413248284223, -42.75510333566816),
            (177.407673659417, -44.471546605796334),
            (176.58940809511245, -46.18095578091026),
            (175.72884840278266, -47.885484758555855),
            (174.81205988512076, -49.58367135376619),
            (173.83243861741815, -51.273905612708624),
            (172.78119311087207, -52.95574121072587),
            (171.64130903910598, -54.625361215229724),
            (170.41560899457167, -56.28647419580335),
            (169.08373088867933, -57.93420475768521),
            (167.62930602018182, -59.5668614442984),
            (166.0243795283944, -61.18062028554268),
            (164.26115705334965, -62.776359315577984),
            (162.30350978708452, -64.34830642665239),
            (160.11788634153672, -65.89157783252615),
            (157.66232733899088, -67.40109715863518),
            (154.88126113623596, -68.86722808467104),
            (160.1325459675333, -69.06048810117184),
            (162.5883735575569, -67.5152692747083),
            (164.74985524368935, -65.9397497607168),
            (166.6843566389666, -64.34111371291355),
            (168.3999709466183, -62.71805533391731),
            (169.94378551545861, -61.077752113025916),
            (171.3430337906186, -59.42214751260288),
            (172.6342022987177, -57.75707684914518),
            (173.80356416208477, -56.07742986626234),
            (174.8814954194563, -54.38819050545594),
            (175.87985821681252, -52.69120887337212),
            (176.80904931895057, -50.986415957829536),
            (177.69231780926836, -49.27817128078806),
            (178.50719394616408, -47.561023088516535),
            (179.27499973531806, -45.83867913785123),
            (180.0, -44.11357146021988),
        ],
    ]


def test_split_polygon_on_antimeridian_ccw_smap_example():
    """SMAP orbit granule (SP_2222_A_002) that crosses both the
    anti-meridian and the prime-meridian. Because it crosses both,
    we have to be careful about how we shift the shape before splitting.
    """
    polygon = Polygon(
        [
            (58.889999, 79.57),
            (82.669998, 73.93),
            (104.139999, 75.870003),
            (127.480003, 77.160004),
            (151.789993, 76.190002),
            (174.910004, 72.160004),
            (-178.990005, 70.089996),
            (-163.029999, 60.09),
            (-162.029999, 59.110001),
            (-155.25, 50.060001),
            (-150.300003, 40.080002),
            (-146.679993, 30.1),
            (-143.770004, 20.08),
            (-141.300003, 10.03),
            (-139.110001, 0.09),
            (-137.059998, -9.93),
            (-135.100006, -19.9),
            (-133.139999, -29.93),
            (-131.070007, -39.939999),
            (-128.759995, -49.93),
            (-125.870003, -59.950001),
            (-121.459999, -69.919998),
            (-104.550003, -82.230003),
            (-81.860001, -85.57),
            (-59.110001, -86.550003),
            (-36.57, -86.779999),
            (-13.32, -86.449997),
            (10.03, -85.209999),
            (33.07, -80.449997),
            (9.92, -73.510002),
            (-11.79, -75.629997),
            (-35.349998, -77.040001),
            (-59.779999, -76.120003),
            (-83.099998, -72.110001),
            (-89.220001, -70.07),
            (-105.339996, -60.080002),
            (-106.300003, -59.099998),
            (-113.169998, -50.09),
            (-118.18, -40.07),
            (-121.860001, -30.040001),
            (-124.779999, -20.059999),
            (-127.269997, -10.1),
            (-129.479996, -0.09),
            (-131.550003, 9.95),
            (-133.529999, 19.92),
            (-135.539993, 29.969999),
            (-137.619995, 39.919998),
            (-139.979996, 49.93),
            (-142.919998, 59.919998),
            (-147.470001, 69.93),
            (-163.820007, 81.889999),
            (173.529999, 85.389999),
            (150.630005, 86.43),
            (128.759995, 86.660004),
            (105.879997, 86.360001),
            (82.620003, 85.150002),
            (58.889999, 79.57),
        ]
    )
    polygons = list(split_polygon_on_antimeridian_ccw(polygon))

    for poly in polygons:
        assert poly.exterior.is_ccw
        assert poly.exterior.is_valid

    # Comparing the polygons directly doesn't seem to work for some reason.
    coords = [list(poly.boundary.coords) for poly in polygons]
    assert coords == [
        [
            (180.0, 70.4327338384591),
            (180.0, 84.3902193311842),
            (173.529999, 85.389999),
            (150.630005, 86.43),
            (128.759995, 86.660004),
            (105.879997, 86.360001),
            (82.620003, 85.150002),
            (58.889999, 79.57),
            (82.669998, 73.93),
            (104.139999, 75.870003),
            (127.480003, 77.160004),
            (151.789993, 76.190002),
            (174.910004, 72.160004),
            (180.0, 70.4327338384591),
        ],
        [
            (-180.0, 84.3902193311842),
            (-180.0, 70.4327338384591),
            (-178.990005, 70.089996),
            (-163.029999, 60.09),
            (-162.029999, 59.110001),
            (-155.25, 50.060001),
            (-150.300003, 40.080002),
            (-146.679993, 30.1),
            (-143.770004, 20.08),
            (-141.300003, 10.03),
            (-139.110001, 0.09),
            (-137.059998, -9.93),
            (-135.100006, -19.9),
            (-133.139999, -29.93),
            (-131.070007, -39.939999),
            (-128.759995, -49.93),
            (-125.870003, -59.950001),
            (-121.45999899999998, -69.919998),
            (-104.550003, -82.230003),
            (-81.86000100000001, -85.57),
            (-59.11000100000001, -86.550003),
            (-36.56999999999999, -86.779999),
            (-13.319999999999993, -86.449997),
            (10.029999999999973, -85.209999),
            (33.06999999999999, -80.449997),
            (9.920000000000016, -73.510002),
            (-11.79000000000002, -75.629997),
            (-35.34999800000003, -77.040001),
            (-59.779998999999975, -76.120003),
            (-83.09999800000003, -72.110001),
            (-89.22000100000002, -70.07),
            (-105.33999599999999, -60.080002),
            (-106.300003, -59.099998),
            (-113.16999800000002, -50.09),
            (-118.18, -40.07),
            (-121.86000100000001, -30.040001),
            (-124.779999, -20.059999),
            (-127.26999699999999, -10.1),
            (-129.479996, -0.09),
            (-131.550003, 9.95),
            (-133.529999, 19.92),
            (-135.539993, 29.969999),
            (-137.619995, 39.919998),
            (-139.979996, 49.93),
            (-142.919998, 59.919998),
            (-147.470001, 69.93),
            (-163.820007, 81.889999),
            (-180.0, 84.3902193311842),
        ],
    ]


def test_split_polygon_on_antimeridian_ccw_multiple_wraps():
    """A thin ribbon spiralling ~1.8 times around the earth.

    It crosses the antimeridian twice in the same direction, so it has to be
    cut on 180 and 540 once shifted, rather than just once.
    """
    polygon = Polygon(
        [
            (30.0, -60.0),
            (90.0, -50.0),
            (150.0, -40.0),
            (-150.0, -30.0),
            (-90.0, -20.0),
            (-30.0, -10.0),
            (30.0, 0.0),
            (90.0, 10.0),
            (150.0, 20.0),
            (-150.0, 30.0),
            (-90.0, 40.0),
            (-30.0, 50.0),
            (-30.0, 60.0),
            (-90.0, 50.0),
            (-150.0, 40.0),
            (150.0, 30.0),
            (90.0, 20.0),
            (30.0, 10.0),
            (-30.0, 0.0),
            (-90.0, -10.0),
            (-150.0, -20.0),
            (150.0, -30.0),
            (90.0, -40.0),
            (30.0, -50.0),
        ]
    )
    polygons = list(split_polygon_on_antimeridian_ccw(polygon))

    for poly in polygons:
        assert poly.exterior.is_ccw
        assert poly.exterior.is_valid

    # Comparing the polygons directly doesn't seem to work for some reason.
    coords = [list(poly.boundary.coords) for poly in polygons]
    assert coords == [
        [
            (180.0, -35.0),
            (180.0, -25.0),
            (150.0, -30.0),
            (90.0, -40.0),
            (30.0, -50.0),
            (30.0, -60.0),
            (90.0, -50.0),
            (150.0, -40.0),
            (180.0, -35.0),
        ],
        [
            (-180.0, -25.0),
            (-180.0, -35.0),
            (-150.0, -30.0),
            (-90.0, -20.0),
            (-30.0, -10.0),
            (30.0, 0.0),
            (90.0, 10.0),
            (150.0, 20.0),
            (180.0, 25.0),
            (180.0, 35.0),
            (150.0, 30.0),
            (90.0, 20.0),
            (30.0, 10.0),
            (-30.0, 0.0),
            (-90.0, -10.0),
            (-150.0, -20.0),
            (-180.0, -25.0),
        ],
        [
            (-180.0, 35.0),
            (-180.0, 25.0),
            (-150.0, 30.0),
            (-90.0, 40.0),
            (-30.0, 50.0),
            (-30.0, 60.0),
            (-90.0, 50.0),
            (-150.0, 40.0),
            (-180.0, 35.0),
        ],
    ]


def test_split_polygon_on_antimeridian_fixed_size_alos2_example():
    """Example from ALOS2: ALOS2014555550-140830"""
    polygon = Polygon(
        [
            (-164.198, -82.125),
            (172.437, -83.885),
            (165.618, -80.869),
            (-176.331, -79.578),
            (-164.198, -82.125),
        ]
    )
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
            (-180.0, -79.84040535150407),
            (-180.0, -83.31530686924889),
            (-164.198, -82.125),
        ],
        [
            (180.0, -83.31530686924889),
            (180.0, -79.84040535150407),
            (165.618, -80.869),
            (172.437, -83.885),
            (180.0, -83.31530686924889),
        ],
    ]
