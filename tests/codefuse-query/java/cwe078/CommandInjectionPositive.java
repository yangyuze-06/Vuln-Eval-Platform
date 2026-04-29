// Positive test case for CWE-078 Command Injection.
// User-controlled input is passed to a command execution API.
package cwe078;

import java.io.IOException;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class CommandInjectionPositive extends HttpServlet {
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        String host = request.getParameter("host");
        Runtime.getRuntime().exec("ping -c 1 " + host);
        response.getWriter().println("done");
    }
}
