// Positive test case for CWE-079 Cross-Site Scripting.
// User-controlled input is written to the HTTP response.
package cwe079;

import java.io.IOException;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class XssPositive extends HttpServlet {
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        String name = request.getParameter("name");
        response.getWriter().println("<p>Hello " + name + "</p>");
    }
}
