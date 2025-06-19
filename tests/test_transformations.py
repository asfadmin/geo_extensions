import shapely.geometry
import strategies
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from shapely.geometry import Polygon

from geo_extensions.transformations import (
    drop_z_coordinate,
    simplify_polygon,
    split_polygon_on_antimeridian_ccw,
    split_polygon_on_antimeridian_fixed_size,
)


def test_simplify():
    polygon = Polygon([
        (20, 0),
        (20, 0),
        (20, 10),
        (0, 10),
        (0, 0),
        (20, 0),
    ])
    assert list(simplify_polygon(0.01)(polygon)) == [
        Polygon([
            (20, 0),
            (20, 10),
            (0, 10),
            (0, 0),
            (20, 0),
        ]),
    ]


def test_simplify_line():
    polygon = Polygon([
        (20, 0),
        (20, 10),
        (20, 10),
        (20, 0),
        (20, 0),
    ])
    assert list(simplify_polygon(0.01)(polygon)) == [
        Polygon([
            (20, 0),
            (20, 10),
            (20, 10),
            (20, 0),
        ]),
    ]

    assert list(simplify_polygon(0.01, preserve_topology=False)(polygon)) == [
        Polygon([]),
    ]


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
        ]),
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


def test_split_polygon_on_antimeridian_ccw_sentinel_ocn_example():
    """Sentinel-1 granule: S1A_WV_OCN__2SSV_20250417T170934_20250417T172302_058799_07490A_662C"""
    polygon = Polygon([
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
    ])
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
            (-180.0, -38.24789031991539),
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
            (180.0, -38.24789031991539),
            (179.59202341272203, -39.307739657248156),
            (178.90089160626383, -41.03375212942789),
            (178.1741324828422, -42.75510333566816),
            (177.40767365941701, -44.471546605796334),
            (176.5894080951125, -46.18095578091026),
            (175.72884840278266, -47.885484758555855),
            (174.8120598851208, -49.58367135376619),
            (173.83243861741812, -51.273905612708624),
            (172.7811931108721, -52.95574121072587),
            (171.64130903910598, -54.625361215229724),
            (170.4156089945717, -56.28647419580335),
            (169.08373088867938, -57.93420475768521),
            (167.62930602018184, -59.5668614442984),
            (166.02437952839443, -61.18062028554268),
            (164.26115705334962, -62.776359315577984),
            (162.30350978708452, -64.34830642665239),
            (160.11788634153675, -65.89157783252615),
            (157.66232733899085, -67.40109715863518),
            (154.88126113623593, -68.86722808467104),
            (160.13254596753336, -69.06048810117184),
            (162.5883735575569, -67.5152692747083),
            (164.74985524368935, -65.9397497607168),
            (166.68435663896662, -64.34111371291355),
            (168.39997094661828, -62.71805533391731),
            (169.94378551545856, -61.077752113025916),
            (171.34303379061862, -59.42214751260288),
            (172.6342022987177, -57.75707684914518),
            (173.80356416208474, -56.07742986626234),
            (174.88149541945631, -54.38819050545594),
            (175.87985821681252, -52.69120887337212),
            (176.80904931895054, -50.986415957829536),
            (177.6923178092684, -49.27817128078806),
            (178.50719394616408, -47.561023088516535),
            (179.27499973531803, -45.83867913785123),
            (180.0, -44.11357146021988),
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
