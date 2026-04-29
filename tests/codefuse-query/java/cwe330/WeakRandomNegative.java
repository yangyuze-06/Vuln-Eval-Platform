// Negative test case for CWE-330 Insufficient Randomness.
// SecureRandom is not reported by this checker.
package cwe330;

import java.security.SecureRandom;

public class WeakRandomNegative {
    public int createTokenPart() {
        return new SecureRandom().nextInt();
    }
}
