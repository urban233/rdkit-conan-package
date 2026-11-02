#include "check.h"
#include <GraphMol/SmilesParse/SmilesParse.h>
#include <GraphMol/MolDraw2D/MolDraw2DCairo.h>
#include <memory>
#include <string>

int main() {
  std::unique_ptr<RDKit::RWMol> molecule(RDKit::SmilesToMol("CCO"));
  RDKit::MolDraw2DCairo drawing(250, 200);
  drawing.drawMolecule(*molecule);
  drawing.finishDrawing();
  check(drawing.getDrawingText().compare(0, 8, std::string("\x89PNG\r\n\x1a\n", 8)) == 0,
        "Invalid PNG output");
}
