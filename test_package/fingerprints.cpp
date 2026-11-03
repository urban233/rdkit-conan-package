#include "check.h"
#include <GraphMol/SmilesParse/SmilesParse.h>
#include <GraphMol/Fingerprints/MorganFingerprints.h>
#include <DataStructs/ExplicitBitVect.h>
#include <memory>

int main() {
  std::unique_ptr<RDKit::RWMol> molecule(RDKit::SmilesToMol("CCO"));
  std::unique_ptr<ExplicitBitVect> fingerprint(
      RDKit::MorganFingerprints::getFingerprintAsBitVect(*molecule, 2, 2048));
  check(fingerprint->getNumBits() == 2048, "Incorrect fingerprint size");
  check(fingerprint->getNumOnBits() == 6, "Incorrect ethanol fingerprint");
}
