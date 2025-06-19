from shapely.geometry import Polygon

from geo_extensions import default_transformer


def test_default_transformer(data_path):
    wkt_path = data_path / "OPERA_L2_RTC-S1_T114-243299-IW1_20230722T122534Z_20230818T184635Z_S1A_30_v0.4.wkt"

    polygons = default_transformer.from_wkt(wkt_path.read_text())
    assert polygons == [
        Polygon([
            (-64.18242781701073, 80.92318071697005),
            (-68.40445755029818, 81.31609026531473),
            (-68.93161319601728, 81.16999707795055),
            (-64.74688665108201, 80.78217738556877),
            (-64.18242781701073, 80.92318071697005),
        ]),
    ]
