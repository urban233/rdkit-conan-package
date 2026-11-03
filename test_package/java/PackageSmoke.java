import org.RDKit.ExplicitBitVect;
import org.RDKit.RDKFuncs;
import org.RDKit.RWMol;

public final class PackageSmoke {
    public static void main(String[] args) {
        System.loadLibrary("GraphMolWrap");
        RWMol molecule = RWMol.MolFromSmiles("OCC");
        if (molecule == null || molecule.getNumAtoms() != 3 || !molecule.MolToSmiles().equals("CCO")) {
            throw new IllegalStateException("Java molecule parsing/canonicalization failed");
        }
        ExplicitBitVect fingerprint = RDKFuncs.RDKFingerprintMol(molecule);
        if (fingerprint.getNumBits() != 2048 || fingerprint.getNumOnBits() == 0) {
            throw new IllegalStateException("Java fingerprint generation failed");
        }
        fingerprint.delete();
        molecule.delete();
        System.out.println("Packaged Java bindings passed");
    }
}
