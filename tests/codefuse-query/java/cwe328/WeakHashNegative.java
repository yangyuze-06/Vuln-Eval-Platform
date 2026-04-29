// Negative test case for CWE-328 Weak Hash Algorithm.
// SHA-256 is not reported by this checker.
package cwe328;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

public class WeakHashNegative {
    public MessageDigest createDigest() throws NoSuchAlgorithmException {
        return MessageDigest.getInstance("SHA-256");
    }
}
