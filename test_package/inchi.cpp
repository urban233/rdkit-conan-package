#include "check.h"
#include <GraphMol/SmilesParse/SmilesParse.h>
#include <GraphMol/inchi.h>
#include <memory>

int main() {
  std::unique_ptr<RDKit::RWMol> molecule(RDKit::SmilesToMol("CCO"));
  RDKit::ExtraInchiReturnValues result;
  check(RDKit::MolToInchi(*molecule, result) == "InChI=1S/C2H6O/c1-2-3/h3H,2H2,1H3",
        "InChI generation failed");
}
