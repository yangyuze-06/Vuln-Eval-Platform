// Positive test case for CWE-330 Insufficient Randomness.
// java.util.Random is not suitable for security-sensitive randomness.
package cwe330;

import java.util.Random;

public class WeakRandomPositive {
    public int createTokenPart() {
        return new Random().nextInt();
    }
}
