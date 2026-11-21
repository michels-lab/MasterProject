"""Synthetic native-polyMesh FS-C04 split cell mapping tests; NO OpenFOAM."""
from __future__ import annotations
from pathlib import Path
import tempfile
import unittest

from audit_fs_c04_split_cells import (
    _foam_list, read_mesh, match_region, cell_volume_m3,
)


def _foam_file(name:str, data:list)->str:
    header=(f"FoamFile {{ version 2.0; format ascii; "
            f"class labelList; object {name}; }}\n"
            f"{len(data)}\n(\n")
    if name=="points":
        body="\n".join("("+ " ".join(map(str,point)) +")" for point in data)
    elif name=="faces":
        body="\n".join("4("+ " ".join(map(str,face)) +")" for face in data)
    else:
        body="\n".join(str(x) for x in data)
    return header+body+"\n)\n"


def _grid_geometry(cubes:list[int], reverse_points:bool=False,
                   reverse_cells:bool=False):
    """Generate connected chain of hexa cells; no CFD and no external libs."""
    positions={(x,y,z):i for i,(x,y,z) in enumerate(
        (x,y,z) for x in range(4) for y in range(2) for z in range(2)
    )}
    corners=[]
    for i in cubes:
        xyz=[
            (i,0,0),(i,0,1),(i,1,1),(i,1,0),
            (i+1,0,0),(i+1,0,1),(i+1,1,1),(i+1,1,0)
        ]
        corners.append(tuple(positions[t] for t in xyz))
    if reverse_cells:
        corners=list(reversed(corners))
    face_template=[
        [0,3,2,1],[4,5,6,7],[0,1,5,4],
        [1,2,6,5],[2,3,7,6],[3,0,4,7],
    ]
    built={}
    for cell_id,v in enumerate(corners):
        for tpl in face_template:
            face=tuple(v[x] for x in tpl)
            key=tuple(sorted(face))
            if key in built:
                built[key][2]=cell_id
            else:
                built[key]=[face,cell_id,None]
    # OpenFOAM requires first nInternalFaces followed by boundary faces.
    ordered=(list(v for v in built.values() if v[2] is not None)+
             list(v for v in built.values() if v[2] is None))
    faces=[v[0] for v in ordered]
    owners=[v[1] for v in ordered]
    neighbours=[v[2] for v in ordered if v[2] is not None]

    points=[None]*len(positions)
    for xyz,idx in positions.items():
        points[idx]=xyz
    if reverse_points:
        old_to_new={old:len(points)-1-old for old in range(len(points))}
        faces=[tuple(old_to_new[x] for x in face) for face in faces]
        points=list(reversed(points))
    return points,faces,owners,neighbours


def _write_mesh(path:Path, cubes:list[int], *,
                reverse_points:bool=False,reverse_cells:bool=False):
    path.mkdir(parents=True)
    points,faces,owner,neighbour=_grid_geometry(
        cubes,reverse_points,reverse_cells
    )
    for name,vals in zip(("points","faces","owner","neighbour"),
                         (points,faces,owner,neighbour)):
        (path/name).write_text(_foam_file(name,vals))


class SplitGeometryTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix="fs-c04-split-")
        self.addCleanup(temp.cleanup)
        root=Path(temp.name)
        self.parent=root/"parent"
        self.fluid=root/"fluid"
        self.mold=root/"mold"
        _write_mesh(self.parent,[0,1,2])
        _write_mesh(self.fluid,[0,1],reverse_points=True,reverse_cells=True)
        _write_mesh(self.mold,[2],reverse_points=True)

    def test_reconstruct_parent_to_split_mapping_even_when_renumbered(self):
        p=read_mesh(self.parent,3)
        f=read_mesh(self.fluid,2)
        m=read_mesh(self.mold,1)
        self.assertEqual(match_region(p,f,{0,1}),{0:1,1:0})
        self.assertEqual(match_region(p,m,{2}),{0:2})
        self.assertAlmostEqual(cell_volume_m3(f,0),1.,places=9)
        self.assertAlmostEqual(cell_volume_m3(f,1),1.,places=9)
        self.assertAlmostEqual(cell_volume_m3(m,0),1.,places=9)

    def test_cell_geometry_does_not_mutate_original_mesh(self):
        files=[p for path in (self.parent,self.fluid,self.mold)
               for p in path.iterdir()]
        original={str(f):f.read_bytes() for f in files}
        p=read_mesh(self.parent,3)
        f=read_mesh(self.fluid,2)
        self.assertEqual(len(match_region(p,f,{0,1})),2)
        self.assertEqual({str(t):t.read_bytes() for t in files},original)

    def test_all_mapped_cells_must_belong_to_expected_phase_zone(self):
        parent=read_mesh(self.parent,3)
        fluid=read_mesh(self.fluid,2)
        with self.assertRaisesRegex(ValueError,"split-region cell not found"):
            match_region(parent,fluid,{0,2})

    def test_different_mesh_geometry_rejected(self):
        ff=self.fluid/"points"
        s=ff.read_text()
        self.assertIn("(2 0 1)",s)
        ff.write_text(s.replace("(2 0 1)","(2.5 0 1)",1))
        parent=read_mesh(self.parent,3)
        child=read_mesh(self.fluid,2)
        with self.assertRaisesRegex(ValueError,"split-region cell not found"):
            match_region(parent,child,{0,1})

    def test_binary_poly_mesh_rejected_without_guessing(self):
        ff=self.fluid/"points"
        ff.write_text(ff.read_text().replace("format ascii;","format binary;"))
        with self.assertRaisesRegex(ValueError,"not ASCII"):
            read_mesh(self.fluid,2)

    def test_invalid_native_face_owner_and_mesh_count_rejected(self):
        ff=self.fluid/"owner"
        ff.write_text(ff.read_text().replace("\n0\n","\n9\n",1))
        with self.assertRaisesRegex(ValueError,"cell label out of bounds"):
            read_mesh(self.fluid,2)
        with self.assertRaisesRegex(ValueError,"cell label out of bounds"):
            read_mesh(self.fluid,3)

    def test_missing_required_native_mesh_file_rejected(self):
        (self.fluid/"neighbour").unlink()
        with self.assertRaisesRegex(ValueError,"missing/untrusted"):
            read_mesh(self.fluid,2)

    def test_nonhexahedral_or_overlapping_cell_rejected(self):
        f=self.fluid/"faces"
        s=f.read_text().replace("4(","3(",1)
        f.write_text(s)
        with self.assertRaisesRegex(ValueError,"unexpected OpenFOAM face size"):
            read_mesh(self.fluid,2)

    def test_numeric_point_quantization_can_compare_index_free(self):
        # A difference smaller than 1 nanometre is beneath the resolution
        # of geometric identity; cells are otherwise verified by 8 corners.
        ff=self.fluid/"points"
        s=ff.read_text()
        self.assertIn("(2 0 1)",s)
        ff.write_text(s.replace("(2 0 1)","(2.0000000002 0 1)",1))
        p=read_mesh(self.parent,3)
        f=read_mesh(self.fluid,2)
        self.assertEqual(match_region(p,f,{0,1}),{0:1,1:0})


if __name__=="__main__":
    unittest.main()
