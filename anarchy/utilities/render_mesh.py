from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple
import tempfile
import zipfile
from rlbot.utils.rendering.rendering_manager import RenderingManager

from utilities.vectors import Vector3

@dataclass
class Polygon:
    vertices: List[Vector3]
@dataclass
class Color:
    R: int
    G: int
    B: int
@dataclass
class ColoredPolygonGroup:
    name: str
    polygons: List[Polygon]
    color: Color
class ColoredWireframe:
    """Parses a .obj file and renders it inside the arena over time.
    To give your mesh the correct colors, you have to make each differently colored part a separate object/group,
    and name them like this: name_HEXVALUE, for example 'white_FFFFFF'"""
    def __init__(self, file_path: str, scale: float=1, position: Vector3=Vector3(0, 0, 0)):
        self.groups: List[ColoredPolygonGroup] = list()
        self.scale = scale
        self.position = position
        self.polygons_rendered = 0
        self.current_color_group = 0

        file = open(file_path)
        lines = file.readlines()
        vertices: List[Vector3] = list()
        for line in lines:
            if line.startswith("v "):
                s = line.split(" ")
                vertex = Vector3(-float(s[3]), float(s[1]), float(s[2])) * scale + position
                vertices.append(vertex)
        for line in lines:
            if line.startswith("o "):
                data = line.split(" ")[1].split("_")
                rgb = tuple(int(data[1][i:i+2], 16) for i in (0, 2, 4))

                self.groups.append(ColoredPolygonGroup(
                    name=data[0],
                    polygons=list(),
                    color=Color(rgb[0], rgb[1], rgb[2])))
            if line.startswith("f "):
                s = line.split(" ")
                polygon = Polygon(list())

                for face in s[1:] + s[1:1]:
                    vertex_index = int(face.split("/")[0]) - 1
                    polygon.vertices.append(vertices[vertex_index])

                self.groups[-1].polygons.append(polygon)

    def render(self, renderer: RenderingManager, polygons_per_tick=100):
        if self.current_color_group < len(self.groups):
            unique_group_name = str(self.polygons_rendered) + str(self.current_color_group)
            renderer.begin_rendering(unique_group_name)
            group: ColoredPolygonGroup = self.groups[self.current_color_group]
            color = renderer.create_color(255, group.color.R, group.color.G, group.color.B)
            for i in range(polygons_per_tick):
                if self.polygons_rendered < len(group.polygons):
                    renderer.draw_polyline_3d(group.polygons[self.polygons_rendered].vertices, color)
                    self.polygons_rendered += 1
                else:
                    self.polygons_rendered = 0
                    self.current_color_group += 1
                    break
            renderer.end_rendering()


def unzip_and_make_mesh(zip_file: str, obj_file: str) -> ColoredWireframe:
    """Extract a zip file into a temp directory, and create a ColoredMesh from a .obj file inside the archive.
    This needs to be done in order to bypass the Anarchy line limit, because .obj is not a binary file."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpdir = Path(tmpdirname)
        try:
            with zipfile.ZipFile(Path(__file__).absolute().parent / zip_file, 'r') as zip_ref: zip_ref.extractall(tmpdir)
        except:
            with zipfile.ZipFile(str(Path(__file__).absolute().parent / zip_file), 'r') as zip_ref: zip_ref.extractall(tmpdir)
        return ColoredWireframe(tmpdir / obj_file, 70, Vector3(3500, 0, 0))