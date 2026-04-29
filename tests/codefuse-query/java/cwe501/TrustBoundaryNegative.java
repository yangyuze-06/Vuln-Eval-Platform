// Negative test case for CWE-501 Trust Boundary Violation.
// Trusted session state is populated from a local constant value.
package cwe501;

import java.io.IOException;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class TrustBoundaryNegative extends HttpServlet {
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        String user = "system";
        request.getSession().setAttribute("user", user);
    }
}
