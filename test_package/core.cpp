#include "check.h"
#include <GraphMol/SmilesParse/SmilesParse.h>
#include <GraphMol/SmilesParse/SmilesWrite.h>
#include <GraphMol/Substruct/SubstructMatch.h>
#include <RDGeneral/versions.h>
#include <memory>
#include <string>

int main() {
  check(std::string(RDKit::rdkitVersion) == EXPECTED_RDKIT_VERSION, "Wrong runtime version");
  std::unique_ptr<RDKit::RWMol> molecule(RDKit::SmilesToMol("OCC"));
  check(molecule && molecule->getNumAtoms() == 3, "SMILES parsing failed");
  check(RDKit::MolToSmiles(*molecule) == "CCO", "Canonicalization failed");
  std::unique_ptr<RDKit::RWMol> query(RDKit::SmartsToMol("[OX2H]"));
  check(RDKit::SubstructMatch(*molecule, *query).size() == 1, "Substructure matching failed");
}
