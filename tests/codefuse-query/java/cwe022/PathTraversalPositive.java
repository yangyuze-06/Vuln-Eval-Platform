// Positive test case for CWE-022 Path Traversal.
// User-controlled input is used to build a filesystem path.
package cwe022;

import java.io.FileInputStream;
import java.io.IOException;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class PathTraversalPositive extends HttpServlet {
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        String name = request.getParameter("file");
        FileInputStream in = new FileInputStream("/var/www/files/" + name);
        response.getOutputStream().write(in.read());
        in.close();
    }
}
