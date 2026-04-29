// Positive test case for CWE-501 Trust Boundary Violation.
// User-controlled input is written into trusted session state.
package cwe501;

import java.io.IOException;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class TrustBoundaryPositive extends HttpServlet {
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        String user = request.getParameter("user");
        request.getSession().setAttribute("user", user);
    }
}
