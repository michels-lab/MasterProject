"""Software tests of recovery contracts; no network, archive download or solver."""
import copy
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from recover_published_200s import validate_manifest, safe_members, entries, checked_destination, validate_report

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.m={"case":"C14-3DB-200s","kind":"fixed_lab_scientific_results",
                "solver_steps":200000,"final_time_s":200,"time_mode":"fixed",
                "archive_sha256":"a"*64,"report_sha256":"b"*64,
                "solver_log_sha256":"c"*64,"complete":True,
                "native_runtime_coverage_complete":True,"volume_fields_included":False,
                "archive_bytes":4,"parts":[{"name":"archive.tar.gz.part000000","bytes":4,"sha256":"d"*64}]}
        self.e=copy.deepcopy(self.m)

    def test_valid_manifest(self):
        validate_manifest(self.m,self.e)

    def test_bad_order_size_and_report(self):
        for key,value in (("name","../wrong"),("bytes",5),("sha256","bad")):
            m=copy.deepcopy(self.m)
            m["parts"][0][key]=value
            with self.assertRaises(ValueError):
                validate_manifest(m,self.e)
        m=copy.deepcopy(self.m)
        m["report_sha256"]="e"*64
        with self.assertRaises(ValueError):
            validate_manifest(m,self.e)

    def archive(self,root,names,linked=False):
        path=root/"data.tar.gz"
        with tarfile.open(path,"w:gz") as t:
            for name in names:
                info=tarfile.TarInfo(name)
                if linked:
                    info.type=tarfile.SYMTYPE
                    info.linkname="/tmp"
                    t.addfile(info)
                else:
                    info.size=3
                    t.addfile(info,io.BytesIO(b"abc"))
        return path

    def test_safe_and_size_limit(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.archive(Path(d),["C14-3DB-200s/report"])
            self.assertEqual(safe_members(p,self.m["case"],3),3)
            with self.assertRaises(ValueError):
                safe_members(p,self.m["case"],2)

    def test_traversal_wrong_case_duplicate_and_link(self):
        for names,linked in [
            (["C14-3DB-200s/../x"],False),(["another/report"],False),
            (["/tmp/x"],False),(["C14-3DB-200s/r"]*2,False),
            (["C14-3DB-200s/r"],True)]:
            with tempfile.TemporaryDirectory() as d:
                p=self.archive(Path(d),names,linked)
                with self.assertRaises(ValueError):
                    safe_members(p,self.m["case"],100)

    def test_manifest_mode_metadata_and_steps(self):
        for key,value in (("mpi_ranks",8),("max_dt_s",.025),("archive_bytes",5),("part_count",2)):
            e={**self.e,key:value}
            with self.assertRaises(ValueError):validate_manifest(self.m,e)
        for value in (0,True,-1):
            m={**self.m,"solver_steps":value}
            with self.assertRaises(ValueError):validate_manifest(m,m)

    def test_complete_index_missing_pin_and_duplicate(self):
        e={**self.e,"sha":"a"*40,"manifest_blob_sha":"b"*40}
        self.assertEqual(entries({"branches":[e]}),[e])
        with self.assertRaises(ValueError):entries({"branches":[{**e,"sha":""}]})
        with self.assertRaises(ValueError):entries({"branches":[e,e]})

    def test_linked_destination_parent(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);repo=root/"repo";repo.mkdir()
            real=root/"real";real.mkdir();link=root/"link";link.symlink_to(real,target_is_directory=True)
            self.assertEqual(checked_destination(repo,real/"new"),real/"new")
            with self.assertRaises(ValueError):checked_destination(repo,link/"new")

    def test_file_as_parent_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.archive(Path(d),[self.m["case"]+"/a",self.m["case"]+"/a/b"])
            with self.assertRaises(ValueError):safe_members(p,self.m["case"],100)

    def test_report_case_and_coverage(self):
        report={"case":self.m["case"],"solver_completed":True,"solver_steps":200000,
                "final_time_s":200,"runtime_audit":{"native_runtime_coverage_complete":True,"errors":[]}}
        validate_report(report,self.m)
        with self.assertRaises(ValueError):validate_report({**report,"case":"B14-2D-200s"},self.m)
        with self.assertRaises(ValueError):validate_report({**report,"physical_validation":True},self.m)

if __name__=="__main__":
    unittest.main()
