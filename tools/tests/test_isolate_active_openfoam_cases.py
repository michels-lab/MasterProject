#!/usr/bin/env python3
"""Real disposable Git integration tests: NEVER use the investigator's WSL."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT=Path(__file__).resolve().parents[1]/"isolate_active_openfoam_cases.py"
spec=importlib.util.spec_from_file_location("isolate_active_openfoam_cases",SCRIPT)
assert spec and spec.loader
iso=importlib.util.module_from_spec(spec)
spec.loader.exec_module(iso)


def run(*args: str) -> str:
    result=subprocess.run(["git",*map(str,args)],check=True,text=True,
                          capture_output=True)
    return result.stdout.strip()


def fixture(have_contraction:bool=True):
    temp=tempfile.TemporaryDirectory()
    workspace=Path(temp.name)/"OpenFOAM"
    workspace.mkdir()
    remote=Path(temp.name)/"remote/michels-lab/MasterProject.git"
    remote.parent.mkdir(parents=True)
    run("init","--bare","-b","main",remote)
    repo=workspace/"MasterProject"
    run("clone",remote,repo)
    run("-C",repo,"config","user.email","fixture@example.invalid")
    run("-C",repo,"config","user.name","Isolation Fixture")
    (repo/"README.md").write_text("original source snapshot\n")
    run("-C",repo,"add","README.md")
    run("-C",repo,"commit","-m","baseline")
    run("-C",repo,"push","-u","origin","main")
    run("-C",repo,"checkout","-b","research/fs-c02-metal-air-vof-20261117")
    (repo/"CONTRACTION.txt").write_text("live contraction source\n")
    fs_source=repo/"freesurface/FS-C06_vof_solidification/README.md"
    fs_source.parent.mkdir(parents=True)
    fs_source.write_text("committed FS-C06 native contraction source\n")
    run("-C",repo,"add","CONTRACTION.txt","freesurface/FS-C06_vof_solidification/README.md")
    run("-C",repo,"commit","-m","contraction")
    run("-C",repo,"push","-u","origin","research/fs-c02-metal-air-vof-20261117")
    run("-C",repo,"checkout","main")
    if have_contraction:
        run("-C",repo,"worktree","add",workspace/"FS_C02_WORKTREE",
            "research/fs-c02-metal-air-vof-20261117")
    for name in iso.SAVED_RUNS:
        d=workspace/name
        d.mkdir()
        (d/"KEEP_CFD_FIELDS").write_text("untouchable native run\n")
    return temp,repo,workspace


class ConcurrentOpenfoamIsolationTests(unittest.TestCase):
    def test_plan_readonly_apply_and_idempotency_without_active_run_changes(self):
        tmp,repo,wsl=fixture()
        try:
            (repo/"UNTRACKED_WHILE_RUNNING").write_text("retain\n")
            (wsl/"FS_C02_WORKTREE/LIVE_MONITOR").write_text("retain\n")
            initial_main=run("-C",repo,"rev-parse","HEAD")
            original_contraction=run("-C",wsl/"FS_C02_WORKTREE","rev-parse","HEAD")
            plan=iso.plan(repo)
            self.assertEqual([x["action"] for x in plan["worktrees"]],
                             ["CREATE_FROM_ORIGIN_MAIN_SNAPSHOT",
                              "CREATE_FROM_ORIGIN_MAIN_SNAPSHOT","EXISTING_PRESERVED"])
            self.assertFalse((wsl/"C3D04_A_WORKTREE").exists())
            applied=iso.apply(repo,plan)
            self.assertEqual(applied["operation"],"APPLIED_AND_VERIFIED")
            self.assertEqual([x["action"] for x in applied["worktrees"]],
                             ["EXISTING_PRESERVED"]*3)
            for folder,branch in [("C3D04_A_WORKTREE","work/c3d04-a-isolated"),
                                  ("C3D05_B_WORKTREE","work/c3d05-b-isolated")]:
                wt=wsl/folder
                self.assertEqual(run("-C",wt,"branch","--show-current"),branch)
                self.assertEqual(run("-C",wt,"rev-parse","HEAD"),initial_main)
                self.assertNotEqual(subprocess.run(
                    ["git","-C",str(wt),"rev-parse","@{upstream}"],
                    capture_output=True).returncode,0)
                self.assertTrue((wt/"README.md").is_file())
            self.assertEqual(run("-C",repo,"rev-parse","HEAD"),initial_main)
            self.assertEqual(run("-C",wsl/"FS_C02_WORKTREE","rev-parse","HEAD"),
                             original_contraction)
            self.assertEqual((wsl/"FS_C02_WORKTREE/LIVE_MONITOR").read_text(),
                             "retain\n")
            self.assertEqual((repo/"UNTRACKED_WHILE_RUNNING").read_text(),
                             "retain\n")
            for name in iso.SAVED_RUNS:
                self.assertEqual((wsl/name/"KEEP_CFD_FIELDS").read_text(),
                                 "untouchable native run\n")
            self.assertEqual(iso.apply(repo,iso.plan(repo))["operation"],
                             "APPLIED_AND_VERIFIED")
        finally:
            tmp.cleanup()

    def test_real_contraction_detached_head_and_dirty_files_are_preserved(self):
        # Reproduce ACTUAL WSL state: FS_C02_WORKTREE used
        # git switch --detach FETCH_HEAD on the research/FS branch.
        tmp,repo,wsl=fixture()
        try:
            fs=wsl/"FS_C02_WORKTREE"
            run("-C",fs,"switch","--detach","HEAD")
            baseline=run("-C",fs,"rev-parse","HEAD")
            (fs/"UNTRACKED_FS_C07_MONITOR").write_text("running\n")
            (fs/"CONTRACTION.txt").write_text("locally modified, DO NOT TOUCH\n")
            checked=iso.plan(repo)
            entry=checked["worktrees"][2]
            self.assertIsNone(entry["branch"])
            self.assertTrue(entry["detached"])
            self.assertEqual(entry["head"],baseline)
            self.assertEqual(entry["remote_lineage_verified"],
                             "refs/remotes/origin/research/fs-c02-metal-air-vof-20261117")
            out=iso.apply(repo,checked)
            self.assertEqual(out["operation"],"APPLIED_AND_VERIFIED")
            self.assertEqual(out["worktrees"][2]["head"],baseline)
            self.assertIsNone(out["worktrees"][2]["actual_branch"])
            self.assertEqual(run("-C",fs,"rev-parse","HEAD"),baseline)
            self.assertEqual(
                subprocess.run(["git","-C",str(fs),"symbolic-ref","-q","HEAD"],
                               capture_output=True).returncode,1)
            self.assertEqual((fs/"UNTRACKED_FS_C07_MONITOR").read_text(),"running\n")
            self.assertEqual((fs/"CONTRACTION.txt").read_text(),
                             "locally modified, DO NOT TOUCH\n")
            self.assertEqual(iso.apply(repo,iso.plan(repo))["operation"],
                             "APPLIED_AND_VERIFIED")
        finally:
            tmp.cleanup()

    def test_unrelated_detached_commit_blocks_before_A_B_worktree_writes(self):
        tmp,repo,wsl=fixture()
        try:
            fs=wsl/"FS_C02_WORKTREE"
            # main does not have the committed FS-C06 contraction overlay.
            run("-C",fs,"switch","--detach","main")
            with self.assertRaisesRegex(iso.Blocked,"source marker absent"):
                iso.plan(repo)
            self.assertFalse((wsl/"C3D04_A_WORKTREE").exists())
            self.assertFalse((wsl/"C3D05_B_WORKTREE").exists())
        finally:
            tmp.cleanup()

    def test_detached_nonancestor_with_FSC06_marker_is_refused(self):
        tmp,repo,wsl=fixture()
        try:
            fs=wsl/"FS_C02_WORKTREE"
            run("-C",fs,"switch","--detach","HEAD")
            # A local-only change creates a detached commit not in the remote
            # research branch. Preserve it, but do not claim FS provenance.
            (fs/"CONTRACTION.txt").write_text("experimental lineage divergence\n")
            run("-C",fs,"add","CONTRACTION.txt")
            run("-C",fs,"config","user.email","fixture@example.invalid")
            run("-C",fs,"config","user.name","Isolation Fixture")
            run("-C",fs,"commit","-m","unpublished detached experiment")
            with self.assertRaisesRegex(iso.Blocked,"not an ancestor"):
                iso.plan(repo)
            self.assertFalse((wsl/"C3D04_A_WORKTREE").exists())
            self.assertFalse((wsl/"C3D05_B_WORKTREE").exists())
        finally:
            tmp.cleanup()

    def test_occupied_target_blocks_everything_without_changes(self):
        tmp,repo,wsl=fixture()
        try:
            (wsl/"C3D04_A_WORKTREE").mkdir()
            (wsl/"C3D04_A_WORKTREE/KEEP").write_text("source\n")
            with self.assertRaisesRegex(iso.Blocked,"destination occupied"):
                iso.plan(repo)
            self.assertFalse((wsl/"C3D05_B_WORKTREE").exists())
            self.assertEqual((wsl/"C3D04_A_WORKTREE/KEEP").read_text(),"source\n")
        finally:
            tmp.cleanup()

    def test_missing_existing_contraction_blocks_before_creating_A_or_B(self):
        tmp,repo,wsl=fixture(False)
        try:
            with self.assertRaisesRegex(iso.Blocked,"not registered"):
                iso.plan(repo)
            self.assertFalse((wsl/"C3D04_A_WORKTREE").exists())
            self.assertFalse((wsl/"C3D05_B_WORKTREE").exists())
        finally:
            tmp.cleanup()

    def test_wrong_repository_origin_and_branch_ownership_block(self):
        tmp,repo,wsl=fixture()
        try:
            run("-C",repo,"remote","set-url","origin","/tmp/not-this-project.git")
            with self.assertRaisesRegex(iso.Blocked,"Unexpected remote"):
                iso.plan(repo)
            remote=Path(tmp.name)/"remote/michels-lab/MasterProject.git"
            run("-C",repo,"remote","set-url","origin",remote)
            run("-C",repo,"worktree","add","--no-track","-b",
                "work/c3d04-a-isolated",wsl/"ANOTHER_CASE_A_WORKTREE","origin/main")
            with self.assertRaisesRegex(iso.Blocked,"already checked out"):
                iso.plan(repo)
        finally:
            tmp.cleanup()


if __name__=="__main__":
    unittest.main()
