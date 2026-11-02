#include "check.h"
#include <GraphMol/SmilesParse/SmilesParse.h>
#include <GraphMol/MolOps.h>
#include <GraphMol/DistGeomHelpers/Embedder.h>
#include <GraphMol/ForceFieldHelpers/MMFF/MMFF.h>
#include <cmath>
#include <memory>

int main() {
  std::unique_ptr<RDKit::RWMol> molecule(RDKit::SmilesToMol("CCO"));
  RDKit::MolOps::addHs(*molecule);
  auto parameters = RDKit::DGeomHelpers::ETKDGv3;
  parameters.randomSeed = 42;
  check(RDKit::DGeomHelpers::EmbedMolecule(*molecule, parameters) >= 0, "Embedding failed");
  auto result = RDKit::MMFF::MMFFOptimizeMolecule(*molecule);
  check(result.first == 0 && std::isfinite(result.second), "MMFF optimization failed");
  check(result.second > -10.0 && result.second < 10.0, "Unexpected ethanol energy");
}
