from unittest.mock import patch
from .base import FunctionalTest
from zincbind.models import *
from scripts.add_pdbs import main

class AddingScriptTests(FunctionalTest):

    @patch("scripts.add_pdbs.get_all_pdb_codes")
    @patch("builtins.print")
    def test_can_check_empty_pdbs(self, mock_print, mock_add):
        self.assertEqual(len(Pdb.objects.all()), 8)
        self.assertEqual(len(ZincSite.objects.all()), 4)
        self.assertEqual(len(Residue.objects.all()), 12)
        self.assertEqual(len(Atom.objects.all()), 48)
        mock_add.return_value = [
         "1AAA", "1AAB", "1AAC", "1AAD", "2AAA", "2AAB", "2AAC", "2AAD",
         "1LOL", "2SAM"
        ]
        main()
        mock_print.assert_any_call("There are 10 current PDB codes.")
        mock_print.assert_any_call("There are 2 which have never been checked.")
        for code in mock_add.return_value:
            mock_print.assert_any_call("\tChecking {}...".format(code))
        self.assertEqual(len(Pdb.objects.all()), 10)
        self.assertEqual(len(ZincSite.objects.all()), 4)
        self.assertEqual(len(Residue.objects.all()), 12)
        self.assertEqual(len(Atom.objects.all()), 48)


    @patch("scripts.add_pdbs.get_all_pdb_codes")
    @patch("builtins.print")
    def test_can_ignore_skeleton_pdbs(self, mock_print, mock_add):
        self.assertEqual(len(Pdb.objects.all()), 8)
        self.assertEqual(len(ZincSite.objects.all()), 4)
        self.assertEqual(len(Residue.objects.all()), 12)
        self.assertEqual(len(Atom.objects.all()), 48)
        mock_add.return_value = [
         "1AAA", "1AAB", "1AAC", "1AAD", "2AAA", "2AAB", "2AAC", "2AAD",
         "1LOL", "2SAM", "1A1Q"
        ]
        main()
        mock_print.assert_any_call("There are 11 current PDB codes.")
        mock_print.assert_any_call("There are 3 which have never been checked.")
        for code in mock_add.return_value:
            mock_print.assert_any_call("\tChecking {}...".format(code))
        mock_print.assert_any_call("\tDiscounting 1A1Q - skeleton PDB")
        self.assertEqual(len(Pdb.objects.all()), 11)
        self.assertEqual(len(ZincSite.objects.all()), 4)
        self.assertEqual(len(Residue.objects.all()), 12)
        self.assertEqual(len(Atom.objects.all()), 48)


    @patch("scripts.add_pdbs.get_all_pdb_codes")
    @patch("builtins.print")
    def test_successful_add(self, mock_print, mock_add):
        self.assertEqual(len(Pdb.objects.all()), 8)
        self.assertEqual(len(ZincSite.objects.all()), 4)
        self.assertEqual(len(Residue.objects.all()), 12)
        self.assertEqual(len(Atom.objects.all()), 48)
        mock_add.return_value = [
         "1AAA", "1AAB", "1AAC", "1AAD", "2AAA", "2AAB", "2AAC", "2AAD",
         "1LOL", "2SAM", "1A1Q", "1TON"
        ]
        main()
        mock_print.assert_any_call("There are 12 current PDB codes.")
        mock_print.assert_any_call("There are 4 which have never been checked.")
        for code in mock_add.return_value:
            mock_print.assert_any_call("\tChecking {}...".format(code))
        mock_print.assert_any_call("\t\tAdded <'A247' Site (3 residues)>")
        self.assertEqual(len(Pdb.objects.all()), 12)
        self.assertEqual(len(ZincSite.objects.all()), 5)
        self.assertEqual(len(Residue.objects.all()), 15)
        self.assertEqual(len(Atom.objects.all()), 78)


    @patch("scripts.add_pdbs.get_all_pdb_codes")
    @patch("builtins.print")
    def test_filtering_of_zero_residue_sites(self, mock_print, mock_add):
        self.assertEqual(len(Pdb.objects.all()), 8)
        self.assertEqual(len(ZincSite.objects.all()), 4)
        self.assertEqual(len(Residue.objects.all()), 12)
        self.assertEqual(len(Atom.objects.all()), 48)
        mock_add.return_value = [
         "1AAA", "1AAB", "1AAC", "1AAD", "2AAA", "2AAB", "2AAC", "2AAD",
         "1LOL", "2SAM", "1A1Q", "1TON", "1C1V"
        ]
        main()
        mock_print.assert_any_call("There are 13 current PDB codes.")
        mock_print.assert_any_call("There are 5 which have never been checked.")
        for code in mock_add.return_value:
            mock_print.assert_any_call("\tChecking {}...".format(code))
        mock_print.assert_any_call("\t\tAdded <'A247' Site (3 residues)>")
        mock_print.assert_any_call("\t\tAdded <'H254' Site (3 residues)>")
        mock_print.assert_any_call("\t\tNot adding <'H255' Site (0 residues)>")
        self.assertEqual(len(Pdb.objects.all()), 13)
        self.assertEqual(len(ZincSite.objects.all()), 6)
        self.assertEqual(len(Residue.objects.all()), 18)
        self.assertEqual(len(Atom.objects.all()), 116)
