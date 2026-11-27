"""Software tests of recovery contracts; no network, archive download or solver."""
import copy
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from recover_published_200s import validate_manifest, safe_members

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

if __name__=="__main__":
    unittest.main()
