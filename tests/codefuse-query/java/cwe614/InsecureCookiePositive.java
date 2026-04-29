// Positive test case for CWE-614 Sensitive Cookie Without Secure Flag.
// The cookie is added to the response with Secure explicitly disabled.
package cwe614;

import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServletResponse;

public class InsecureCookiePositive {
    public void addCookie(HttpServletResponse response, String value) {
        Cookie cookie = new Cookie("session", value);
        cookie.setSecure(false);
        response.addCookie(cookie);
    }
}
