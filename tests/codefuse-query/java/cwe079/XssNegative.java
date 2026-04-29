// Negative test case for CWE-079 Cross-Site Scripting.
// The response uses constant content instead of user-controlled input.
package cwe079;

import java.io.IOException;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class XssNegative extends HttpServlet {
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        response.getWriter().println("<p>Hello user</p>");
    }
}
