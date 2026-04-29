// Positive test case for CWE-643 XPath Injection.
// User-controlled input is concatenated into an XPath expression.
package cwe643;

import javax.servlet.http.HttpServletRequest;
import javax.xml.xpath.XPath;
import javax.xml.xpath.XPathExpressionException;
import org.w3c.dom.Document;

public class XPathInjectionPositive {
    public String evaluate(HttpServletRequest request, XPath xpath, Document document)
            throws XPathExpressionException {
        String user = request.getParameter("user");
        String expression = "/users/user[name='" + user + "']/email/text()";

        return xpath.evaluate(expression, document);
    }
}
