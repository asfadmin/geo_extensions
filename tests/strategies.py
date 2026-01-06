import shapely
import shapely.geometry
from hypothesis import assume
from hypothesis import strategies as st


def assume_valid_polygon(polygon):
    assume(polygon.area > 0.01)
    simplified = shapely.remove_repeated_points(polygon.simplify(0))
    assume(len(simplified.exterior.coords) > 4)


@st.composite
def rectangles(
    draw,
    lats=st.floats(min_value=-90, max_value=90),
    lons=st.floats(min_value=-180, max_value=180),
):
    north, south = draw(lats), draw(lats)
    assume(north > south)

    east, west = draw(lons), draw(lons)
    assume(abs(east - west) > 0.001)

    polygon = shapely.geometry.box(east, north, west, south, ccw=True)
    assume_valid_polygon(polygon)

    return polygon
