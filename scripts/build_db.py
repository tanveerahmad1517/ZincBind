#! /usr/bin/env python3

"""When run, this script will build the ZincBind database from scratch."""

import sys
import os
sys.path.append(os.path.join("..", "zincbind"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django; django.setup()
from django.db import transaction
from django.core.management import call_command
from zinc.utilities import *
from zinc.models import Pdb, Metal, Chain, ZincSite, Residue
import atomium
from tqdm import tqdm


def main(reset=False, log=True, json=True):
    # Setup log
    logger = get_log() if log else None

    # Get all PDBs which contain zinc
    if log: logger.info("Getting PDB codes")
    codes = get_zinc_pdb_codes()
    print(f"There are {len(codes)} PDBs with zinc")
    if not reset:
        checked = [p.id for p in Pdb.objects.all()]
        print(f"{len(checked)} have already been checked")
        codes = [code for code in codes if code not in checked]

    # Go through each PDB
    mmcif_count = 0
    for code in tqdm(codes):
        with transaction.atomic():
            # Get PDB
            if log: logger.info("Getting PDB {} object from server".format(code))
            try:
                pdb = atomium.fetch(code)
            except ValueError:
                mmcif_count += 1
                if log: logger.info("Couldn't get {}".format(code))
                continue

            # Which assembly should be used?
            if log: logger.info("Getting best assembly")
            model = pdb.generate_best_assembly()
            metals = model.atoms(is_metal=True)
            while not metals:
                pdb.assemblies.remove(pdb.best_assembly)
                model = pdb.generate_best_assembly()
                metals = model.atoms(is_metal=True)

            # Save the PDB
            if log: logger.info("Saving PDB to database")
            pdb_record = Pdb.create_from_atomium(pdb)

            # Is the PDB usable?
            if log: logger.info("Checking PDB usable")
            if model_is_skeleton(model):
                zincs = model.atoms(element="ZN")
                if log: logger.info("It isn't - saving metals")
                for zinc in zincs:
                    Metal.create_from_atomium(
                     zinc, pdb_record,
                     omission="No residue side chain information in PDB."
                    )
                continue

            # Are any PDB zincs not in assembly
            if log: logger.info("Looking for unused zinc")
            au_zincs = pdb.model.atoms(element="ZN")
            assembly_zinc_ids = [atom.id for atom in model.atoms(element="ZN")]
            for zinc in au_zincs:
                if zinc.id not in assembly_zinc_ids:
                    Metal.create_from_atomium(
                     zinc, pdb_record,
                     omission="Zinc was in asymmetric unit but not biological assembly."
                    )

            # Get zinc clusters
            if log: logger.info("Clustering metals into sites")
            zinc_clusters = cluster_zincs_with_residues(metals)

            # Create chains
            if log: logger.info("Creating chains")
            chains = {}
            for cluster in zinc_clusters:
                for o in cluster["residues"].union(cluster["metals"]):
                    chains[o.chain.id] = o.chain
            for chain_id, chain in chains.items():
                chains[chain_id] = Chain.create_from_atomium(chain, pdb_record)

            # Create binding sites
            for index, cluster in enumerate(zinc_clusters, start=1):
                # Does the cluster even have any residues?
                if len(cluster["residues"]) == 0:
                    if log: logger.info("Not creating site - no residues")
                    Metal.create_from_atomium(
                     zinc, pdb_record,
                     omission="Zinc has no binding residues."
                    )
                    continue
                # Does the cluster have enough liganding atoms?
                atoms = []
                for residue in cluster["residues"]:
                    atoms += [a for a in residue.atoms() if a.liganding]
                if len(atoms) < 3:
                    if log: logger.info(
                     "Not creating site - too few liganding atoms"
                    )
                    for metal in cluster["metals"]:
                        Metal.create_from_atomium(
                         metal, pdb_record, omission="Zinc has too few liganding atoms."
                        )
                    continue

                # Create site record itself
                if log: logger.info("Creating site")
                site = ZincSite.objects.create(
                 id=f"{pdb_record.id}-{index}", pdb=pdb_record,
                 code=create_site_code(cluster["residues"]),
                 copies=cluster["count"]
                )

                # Create metals
                if log: logger.info("Creating metals")
                for metal in cluster["metals"]:
                    Metal.create_from_atomium(metal, pdb_record, site=site)

                # Create residue records
                if log: logger.info("Creating residues")
                for r in cluster["residues"]:
                    chain = chains[r.chain.id]
                    Residue.create_from_atomium(r, chain, site)
    mmcif = []
    if log: logger.info("{} mmcif files ignored".format(mmcif_count))
    print("{} mmcif files ignored".format(mmcif_count))


    # JSON?
    if json:
        print("Saving JSON")
        sysout = sys.stdout
        with open("data/zinc.json", "w") as f:
            sys.stdout = f
            call_command(
             "dumpdata",  "--exclude=contenttypes", verbosity=0
            )
            sys.stdout = sysout


if __name__ == "__main__":
    main(reset="reset" in sys.argv)
