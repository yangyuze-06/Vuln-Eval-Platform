// Negative test case for CWE-327 Broken/Risky Crypto Algorithm.
// AES/GCM is not reported by this checker.
package cwe327;

import javax.crypto.Cipher;
import java.security.GeneralSecurityException;

public class BrokenCryptoNegative {
    public Cipher createCipher() throws GeneralSecurityException {
        return Cipher.getInstance("AES/GCM/NoPadding");
    }
}
