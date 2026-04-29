// Positive test case for CWE-328 Weak Hash Algorithm.
// MD5 is a weak hash algorithm.
package cwe328;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

public class WeakHashPositive {
    public MessageDigest createDigest() throws NoSuchAlgorithmException {
        return MessageDigest.getInstance("MD5");
    }
}
