#include "check.h"
#include <GraphMol/GraphMol.h>
#include <GraphMol/FileParsers/MolSupplier.h>
#include <cstdlib>
#include <fstream>
#include <memory>
#include <string>

int main() {
  const char *base = std::getenv("RDBASE");
  check(base != nullptr, "Packaged data environment is missing");
  const std::string sdfPath = std::string(base) + "/Data/NCI/first_200.props.sdf";
  std::ifstream sdf(sdfPath, std::ios_base::binary);
  check(sdf.good(), "Packaged SDF data is missing");
  RDKit::v2::FileParsers::SDMolSupplier supplier(&sdf, false);
  check(bool(supplier.next()), "SDF sequential read failed");
  auto tenth = supplier[10];
  check(bool(tenth), "SDF random access failed");
  RDKit::SDMolSupplier byFilename(sdfPath);
  std::unique_ptr<RDKit::ROMol> fromFilename(byFilename[10]);
  check(fromFilename && tenth->getNumAtoms() == fromFilename->getNumAtoms(),
        "Filename and stream suppliers disagree");

  std::ifstream csv(std::string(base) + "/Data/NCI/first_200.tpsa.csv", std::ios_base::binary);
  check(csv.good(), "Packaged SMILES data is missing");
  RDKit::v2::FileParsers::SmilesMolSupplierParams parameters;
  parameters.delimiter = ',';
  RDKit::v2::FileParsers::SmilesMolSupplier smiles(&csv, false, parameters);
  check(bool(smiles.next()) && bool(smiles[10]), "SMILES supplier read/seek failed");
}
