from unittest.mock import Mock, patch, MagicMock
from .base import ZincBindTest
from zincbind.utilities import *
from zincbind.exceptions import RcsbError, AtomiumError

class PdbCodeGrabTests(ZincBindTest):

    @patch("requests.get")
    def test_can_get_all_pdb_codes(self, mock_get):
        response = Mock()
        response.status_code = 200
        response.text = ("<?xml version='1.0' standalone='no' ?>\n<current>\n  "
        "<PDB structureId=\"100D\" />\n  <PDB structureId=\"101D\" />\n  "
        "<PDB structureId=\"101M\" />\n</current>\n'")
        mock_get.return_value = response
        self.assertEqual(get_all_pdb_codes(), ["100D", "101D", "101M"])
        mock_get.assert_called_with("https://www.rcsb.org/pdb/rest/getCurrent")


    @patch("requests.get")
    def test_pdb_obtaining_can_throw_rcsb_error_on_500(self, mock_get):
        response = Mock()
        response.status_code = 500
        mock_get.return_value = response
        with self.assertRaises(RcsbError):
            get_all_pdb_codes()


    @patch("requests.get")
    def test_pdb_obtaining_can_throw_rcsb_error_when_unparsable(self, mock_get):
        response = Mock()
        response.status_code = 200
        response.text = "NONSENSE STRING"
        mock_get.return_value = response
        with self.assertRaises(RcsbError):
            get_all_pdb_codes()



class CheckedPdbRemovalTests(ZincBindTest):

    @patch("zincbind.utilities.Pdb.objects.all")
    def test_can_remove_checked_pdbs(self, mock_filter):
        result_set = Mock()
        mock_filter.return_value = result_set
        result_set.values_list.return_value = ["1AAA", "2AAA", "4AAA"]
        pdbs = ["1AAA", "2AAA", "3AAA", "4AAA", "5AAA"]
        remove_checked_pdbs(pdbs)
        result_set.values_list.assert_called_with("id", flat=True)
        self.assertEqual(pdbs, ["3AAA", "5AAA"])



class PdbTextLoadingTests(ZincBindTest):

    @patch("builtins.open")
    def test_can_get_local_file(self, mock_open):
        with patch.dict("os.environ", {"PDBPATH": "/path/to/pdbs"}):
            open_return = MagicMock()
            mock_file = Mock()
            open_return.__enter__.return_value = mock_file
            mock_file.read.return_value = "returnstring"
            mock_open.return_value = open_return
            filestring = get_pdb_filestring("1ABC")
            mock_open.assert_called_with("/path/to/pdbs/pdb1abc.ent")
            self.assertEqual(filestring, "returnstring")


    @patch("builtins.open")
    @patch("atomium.files.utilities.fetch_string")
    def test_can_fall_back_on_rcsb(self, mock_string, mock_open):
        with patch.dict("os.environ", {"PDBPATH": "/path/to/pdbs"}):
            mock_open.side_effect = FileNotFoundError
            mock_string.return_value = "FILESTRING"
            filestring = get_pdb_filestring("1ABC")
            mock_string.assert_called_with("1ABC")
            self.assertEqual(filestring, "FILESTRING")


    @patch("atomium.files.utilities.fetch_string")
    def test_can_get_pdb_text_from_web(self, mock_string):
        with patch.dict("os.environ", {"PDBPATHX": "/path/to/pdbs"}):
            try:
                del os.environ["PDBPATH"]
            except: pass
            mock_string.return_value = "FILESTRING"
            filestring = get_pdb_filestring("1ABC")
            mock_string.assert_called_with("1ABC")
            self.assertEqual(filestring, "FILESTRING")


    @patch("atomium.files.utilities.fetch_string")
    def test_getting_pdb_from_web_can_throw_error(self, mock_string):
        with patch.dict("os.environ", {"PDBPATHX": "/path/to/pdbs"}):
            try:
                del os.environ["PDBPATH"]
            except: pass
            mock_string.return_value = None
            with self.assertRaises(RcsbError):
                get_pdb_filestring("1ABC")



class ZincInFileCheckingTests(ZincBindTest):

    def test_can_find_zinc_in_file(self):
        self.assertTrue(zinc_in_pdb("\n".join([
         "SEQRES  19 A  235  PRO    ",
         "HET     ZN  A 247       1    ",
         "HETNAM      ZN ZINC ION    "
        ])))


    def test_can_reject_zinc_in_file(self):
        self.assertFalse(zinc_in_pdb("\n".join([
         "SEQRES  19 A  235  PRO    ",
         "HET     MOL  A 247       1    ",
         "HETNAM      ZN ZINC ION    "
        ])))



class PdbLoadingTests(ZincBindTest):

    @patch("atomium.files.pdbstring2pdbdict.pdb_string_to_pdb_dict")
    @patch("atomium.files.pdbdict2pdb.pdb_dict_to_pdb")
    def test_can_get_pdb(self, mock_pdb, mock_dict):
        mock_dict.return_value = {"pdb": "dict"}
        mock_pdb.return_value = "PDB"
        pdb = get_pdb("FILESTRING")
        mock_dict.assert_called_with("FILESTRING")
        mock_pdb.assert_called_with({"pdb": "dict"})
        self.assertEqual(pdb, "PDB")


    @patch("atomium.files.pdbstring2pdbdict.pdb_string_to_pdb_dict")
    @patch("atomium.files.pdbdict2pdb.pdb_dict_to_pdb")
    def test_can_throw_atomium_error(self, mock_pdb, mock_dict):
        mock_dict.side_effect = Exception
        mock_pdb.side_effect = Exception
        with self.assertRaises(AtomiumError):
            get_pdb("FILESTRING")
        mock_dict.side_effect = [{"pdb": "dict"}] * 3
        with self.assertRaises(AtomiumError):
            get_pdb("FILESTRING")
        mock_pdb.side_effect = ["PDB"] * 3
        get_pdb("1ABC")



class SkeletonModelTests(ZincBindTest):

    def setUp(self):
        ZincBindTest.setUp(self)
        self.model = Mock()
        self.atoms = Mock(), Mock(), Mock(), Mock(), Mock()
        self.atoms[0].name.return_value = "N"
        self.atoms[1].name.return_value = "CA"
        self.atoms[2].name.return_value = "C"
        self.atoms[3].name.return_value = "O"
        self.atoms[4].name.return_value = "CB"
        chaina, chainb = Mock(), Mock()
        chaina.atoms.return_value = set(self.atoms[:3])
        chainb.atoms.return_value = set(self.atoms[3:])
        self.model.chains.return_value = set([chaina, chainb])


    def test_can_pass_model(self):
        self.assertFalse(model_is_skeleton(self.model))


    def test_can_fail_model(self):
        self.atoms[4].name.return_value = "CA"
        self.assertTrue(model_is_skeleton(self.model))



class AtomicSolvationTests(ZincBindTest):

    def setUp(self):
        ZincBindTest.setUp(self)
        self.atom = Mock()
        self.atom.element.return_value = "X"
        self.atom.atom_name.return_value = "XX"
        self.atom.charge.return_value = 0
        self.residue = Mock()
        self.atom.residue.return_value = self.residue
        self.residue.name.return_value = "XXX"

        c = 75.312
        on = -37.656
        o_c = -154.808
        n_c = -158.992
        s = -20.92
        gluaspo = -96.232
        hisargn = -98.324


    def test_generic_atom_solvation(self):
        self.assertEqual(atomic_solvation(self.atom), 0)


    def test_carbon_atom_solvation(self):
        self.atom.element.return_value = "C"
        self.assertEqual(atomic_solvation(self.atom), 75.312)


    def test_oxygen_atom_solvation(self):
        self.atom.element.return_value = "O"
        self.assertEqual(atomic_solvation(self.atom), -37.656)


    def test_charged_oxygen_atom_solvation(self):
        self.atom.element.return_value = "O"
        self.atom.charge.return_value = -2
        self.assertEqual(atomic_solvation(self.atom), -154.808)


    def test_glutamate_oxygen_atom_solvation(self):
        self.atom.element.return_value = "O"
        self.atom.name.return_value = "OE1"
        self.assertEqual(atomic_solvation(self.atom), -37.656)
        self.residue.name.return_value = "GLU"
        self.assertEqual(atomic_solvation(self.atom), -96.232)
        self.atom.name.return_value = "OE2"
        self.assertEqual(atomic_solvation(self.atom), -96.232)
        self.atom.name.return_value = "O"
        self.assertEqual(atomic_solvation(self.atom), -37.656)


    def test_aspartate_oxygen_atom_solvation(self):
        self.atom.element.return_value = "O"
        self.atom.name.return_value = "OD1"
        self.assertEqual(atomic_solvation(self.atom), -37.656)
        self.residue.name.return_value = "ASP"
        self.assertEqual(atomic_solvation(self.atom), -96.232)
        self.atom.name.return_value = "OD2"
        self.assertEqual(atomic_solvation(self.atom), -96.232)
        self.atom.name.return_value = "O"
        self.assertEqual(atomic_solvation(self.atom), -37.656)


    def test_nitrogen_atom_solvation(self):
        self.atom.element.return_value = "N"
        self.assertEqual(atomic_solvation(self.atom), -37.656)


    def test_charged_nitrogen_atom_solvation(self):
        self.atom.element.return_value = "N"
        self.atom.charge.return_value = 1
        self.assertEqual(atomic_solvation(self.atom), -158.992)


    def test_lysine_nitrogen_atom_solvation(self):
        self.atom.element.return_value = "N"
        self.atom.name.return_value = "NZ"
        self.assertEqual(atomic_solvation(self.atom), -37.656)
        self.residue.name.return_value = "LYS"
        self.assertEqual(atomic_solvation(self.atom), -158.992)
        self.atom.name.return_value = "N"
        self.assertEqual(atomic_solvation(self.atom), -37.656)


    def test_histidine_nitrogen_atom_solvation(self):
        self.atom.element.return_value = "N"
        self.atom.name.return_value = "ND1"
        self.assertEqual(atomic_solvation(self.atom), -37.656)
        self.residue.name.return_value = "HIS"
        self.assertEqual(atomic_solvation(self.atom), -98.324)
        self.atom.name.return_value = "NE2"
        self.assertEqual(atomic_solvation(self.atom), -98.324)
        self.residue.residue_name.return_value = "HIE"
        self.assertEqual(atomic_solvation(self.atom), -98.324)
        self.residue.residue_name.return_value = "HID"
        self.assertEqual(atomic_solvation(self.atom), -98.324)
        self.atom.name.return_value = "N"
        self.assertEqual(atomic_solvation(self.atom), -37.656)


    def test_arginine_nitrogen_atom_solvation(self):
        self.atom.element.return_value = "N"
        self.atom.name.return_value = "NH1"
        self.assertEqual(atomic_solvation(self.atom), -37.656)
        self.residue.name.return_value = "ARG"
        self.assertEqual(atomic_solvation(self.atom), -98.324)
        self.atom.name.return_value = "NH2"
        self.assertEqual(atomic_solvation(self.atom), -98.324)
        self.atom.name.return_value = "N"
        self.assertEqual(atomic_solvation(self.atom), -37.656)
