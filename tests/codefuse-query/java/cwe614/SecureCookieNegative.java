// Negative test case for CWE-614 Sensitive Cookie Without Secure Flag.
// The cookie is marked Secure before it is added to the response.
package cwe614;

import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServletResponse;

public class SecureCookieNegative {
    public void addCookie(HttpServletResponse response, String value) {
        Cookie cookie = new Cookie("session", value);
        cookie.setSecure(true);
        response.addCookie(cookie);
    }
}
