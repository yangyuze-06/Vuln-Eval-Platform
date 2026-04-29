// Positive test case for CWE-327 Broken/Risky Crypto Algorithm.
// DES is a broken cryptographic algorithm.
package cwe327;

import javax.crypto.Cipher;
import java.security.GeneralSecurityException;

public class BrokenCryptoPositive {
    public Cipher createCipher() throws GeneralSecurityException {
        return Cipher.getInstance("DES/CBC/PKCS5Padding");
    }
}
