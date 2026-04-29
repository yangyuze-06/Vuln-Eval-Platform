// Negative test case for CWE-643 XPath Injection.
// XPath evaluation uses a constant expression instead of user-controlled input.
package cwe643;

import javax.servlet.http.HttpServletRequest;
import javax.xml.xpath.XPath;
import javax.xml.xpath.XPathExpressionException;
import org.w3c.dom.Document;

public class XPathInjectionNegative {
    public String evaluate(HttpServletRequest request, XPath xpath, Document document)
            throws XPathExpressionException {
        request.getParameter("user");
        String expression = "/users/user[name='service']/email/text()";

        return xpath.evaluate(expression, document);
    }
}
