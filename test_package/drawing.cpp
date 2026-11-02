#include "check.h"
#include <GraphMol/SmilesParse/SmilesParse.h>
#include <GraphMol/MolDraw2D/MolDraw2DSVG.h>
#include <memory>
#include <string>

int main() {
  std::unique_ptr<RDKit::RWMol> molecule(RDKit::SmilesToMol("CCO"));
  RDKit::MolDraw2DSVG drawing(250, 200);
  drawing.drawMolecule(*molecule);
  drawing.finishDrawing();
  check(drawing.getDrawingText().find("<svg") != std::string::npos, "SVG output missing");
}
