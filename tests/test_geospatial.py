from satlib.geospatial import split_bbox_on_idl


def test_split_bbox_on_idl_noop():
    bbox = [
        (60, 160),
        (60, 170),
        (70, 170),
        (70, 160),
        (60, 160)
    ]
    assert split_bbox_on_idl(bbox) == [bbox]


def test_split_bbox_on_idl_centered():
    """Polygon is centered on IDL"""
    bbox = [
        (60, 170),
        (60, -170),
        (70, -170),
        (70, 170),
        (60, 170)
    ]
    assert split_bbox_on_idl(bbox) == [
        [[70.0, 179.999], [60.0, 179.999], [60.0, 170.0], [70.0, 170.0]],
        [[60.0, -179.999], [70.0, -179.999], [70.0, -170.0], [60.0, -170.0]]
    ]


def test_split_bbox_on_idl_west():
    """Polygon is mostly west of the IDL"""
    bbox = [
        (60, 170),
        (60, -179),
        (70, -179),
        (70, 170),
        (60, 170)
    ]
    assert split_bbox_on_idl(bbox) == [
        [[70.0, 179.999], [60.0, 179.999], [60.0, 170.0], [70.0, 170.0]],
        [[60.0, -179.999], [70.0, -179.999], [70.0, -179.0], [60.0, -179.0]]
    ]


def test_split_bbox_on_idl_east():
    """Polygon is mostly east of the IDL"""
    bbox = [
        (60, 179),
        (60, -170),
        (70, -170),
        (70, 179),
        (60, 179)
    ]
    assert split_bbox_on_idl(bbox) == [
        [[70.0, 179.999], [60.0, 179.999], [60.0, 179.0], [70.0, 179.0]],
        [[60.0, -179.999], [70.0, -179.999], [70.0, -170.0], [60.0, -170.0]]
    ]


def test_split_bbox_on_idl_alos_example():
    """Example from ALOS mission: ALPSRP237090990-L1.1"""
    bbox = [
        (50.172, 179.648),
        (49.658, 179.794),
        (49.766, -179.255),
        (50.281, -179.392),
        (50.172, 179.648),
    ]
    assert split_bbox_on_idl(bbox) == [
        [[50.21196666666666, 179.999], [49.68139432176656, 179.999], [49.658, 179.79399999999998], [50.172, 179.64800000000002]],
        [[49.68139432176656, -179.999], [50.21196666666666, -179.999], [50.281, -179.392], [49.766, -179.255]]
    ]
