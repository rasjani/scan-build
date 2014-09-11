# -*- coding: utf-8 -*-
#                     The LLVM Compiler Infrastructure
#
# This file is distributed under the University of Illinois Open Source
# License. See LICENSE.TXT for details.

from ...unit import fixtures
import unittest

import os.path
import string
import subprocess
import glob


def _prepare_compilation_db(target_file, target_dir):
    this_dir, _ = os.path.split(__file__)
    path = os.path.normpath(os.path.join(this_dir, '..', 'src'))
    source_dir = os.path.join(path, 'compilation_database')
    source_file = os.path.join(source_dir, target_file + '.in')
    target_file = os.path.join(target_dir, 'compile_commands.json')
    with open(source_file, 'r') as in_handle:
        with open(target_file, 'w') as out_handle:
            for line in in_handle:
                temp = string.Template(line)
                out_handle.write(temp.substitute(path=path))
    return target_file


def prepare_clean_cdb(target_dir):
    return _prepare_compilation_db('build_clean.json', target_dir)


def prepare_regular_cdb(target_dir):
    return _prepare_compilation_db('build_regular.json', target_dir)


def prepare_broken_cdb(target_dir):
    return _prepare_compilation_db('build_brokens.json', target_dir)


def run_beye(directory, args):
    cmd = ['beye', '--output', directory] + args
    child = subprocess.Popen(cmd,
                             universal_newlines=True,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
    output = child.stdout.readlines()
    child.stdout.close()
    child.wait()
    return (child.returncode, output)


class OutputDirectoryTest(unittest.TestCase):

    def test_regular_keeps_report_dir(self):
        with fixtures.TempDir() as tmpdir:
            cdb = prepare_regular_cdb(tmpdir)
            outdir = os.path.join(tmpdir, 'result')
            exit_code, output = run_beye(outdir, ['--input', cdb])
            self.assertTrue(os.path.isdir(outdir))

    def test_clear_deletes_report_dir(self):
        with fixtures.TempDir() as tmpdir:
            cdb = prepare_clean_cdb(tmpdir)
            outdir = os.path.join(tmpdir, 'result')
            exit_code, output = run_beye(outdir, ['--input', cdb])
            self.assertFalse(os.path.isdir(outdir))

    def test_clear_keeps_report_dir_when_asked(self):
        with fixtures.TempDir() as tmpdir:
            cdb = prepare_clean_cdb(tmpdir)
            outdir = os.path.join(tmpdir, 'result')
            exit_code, output = run_beye(outdir,
                                         ['--input', cdb, '--keep-empty'])
            self.assertTrue(os.path.isdir(outdir))


class ExitCodeTest(unittest.TestCase):

    def test_regular_set_exit_code(self):
        with fixtures.TempDir() as tmpdir:
            cdb = prepare_regular_cdb(tmpdir)
            outdir = os.path.join(tmpdir, 'result')
            exit_code, output = run_beye(outdir, ['--input', cdb])
            self.assertTrue(exit_code)

    def test_clear_does_not_set_exit_code(self):
        with fixtures.TempDir() as tmpdir:
            cdb = prepare_clean_cdb(tmpdir)
            outdir = os.path.join(tmpdir, 'result')
            exit_code, output = run_beye(outdir, ['--input', cdb])
            self.assertFalse(exit_code)

    def test_regular_clear_exit_code(self):
        with fixtures.TempDir() as tmpdir:
            cdb = prepare_regular_cdb(tmpdir)
            outdir = os.path.join(tmpdir, 'result')
            exit_code, output = run_beye(outdir,
                                         ['--input', cdb, '--status-bugs'])
            self.assertTrue(exit_code)


class OutputFormatTest(unittest.TestCase):

    @staticmethod
    def get_html_count(directory):
        return len(glob.glob(os.path.join(directory, 'report-*.html')))

    @staticmethod
    def get_plist_count(directory):
        return len(glob.glob(os.path.join(directory, 'report-*.plist')))

    def test_default_creates_html_report(self):
        with fixtures.TempDir() as tmpdir:
            cdb = prepare_regular_cdb(tmpdir)
            outdir = os.path.join(tmpdir, 'result')
            exit_code, output = run_beye(outdir, ['--input', cdb])
            self.assertTrue(os.path.exists(os.path.join(outdir, 'index.html')))
            self.assertEqual(self.get_html_count(outdir), 2)
            self.assertEqual(self.get_plist_count(outdir), 0)

    def test_plist_and_html_creates_html_report(self):
        with fixtures.TempDir() as tmpdir:
            cdb = prepare_regular_cdb(tmpdir)
            outdir = os.path.join(tmpdir, 'result')
            exit_code, output = run_beye(outdir,
                                         ['--input', cdb, '--plist-html'])
            self.assertTrue(os.path.exists(os.path.join(outdir, 'index.html')))
            self.assertEqual(self.get_html_count(outdir), 2)
            self.assertEqual(self.get_plist_count(outdir), 5)

    def test_plist_does_not_creates_html_report(self):
        with fixtures.TempDir() as tmpdir:
            cdb = prepare_regular_cdb(tmpdir)
            outdir = os.path.join(tmpdir, 'result')
            exit_code, output = run_beye(outdir,
                                         ['--input', cdb, '--plist'])
            self.assertFalse(
                os.path.exists(os.path.join(outdir, 'index.html')))
            self.assertEqual(self.get_html_count(outdir), 0)
            self.assertEqual(self.get_plist_count(outdir), 5)


class FailureReportTest(unittest.TestCase):

    def test_broken_creates_failure_reports(self):
        with fixtures.TempDir() as tmpdir:
            cdb = prepare_broken_cdb(tmpdir)
            outdir = os.path.join(tmpdir, 'result')
            exit_code, output = run_beye(outdir, ['--input', cdb])
            self.assertTrue(os.path.isdir(os.path.join(outdir, 'failures')))

    def test_broken_does_not_creates_failure_reports(self):
        with fixtures.TempDir() as tmpdir:
            cdb = prepare_broken_cdb(tmpdir)
            outdir = os.path.join(tmpdir, 'result')
            exit_code, output = run_beye(
                outdir, ['--input', cdb, '--no-failure-reports'])
            self.assertFalse(os.path.isdir(os.path.join(outdir, 'failures')))