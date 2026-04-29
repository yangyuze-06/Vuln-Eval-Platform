// Negative test case for CWE-022 Path Traversal.
// Filesystem access uses a constant path instead of user-controlled input.
package cwe022;

import java.io.FileInputStream;
import java.io.IOException;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class PathTraversalNegative extends HttpServlet {
    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        FileInputStream in = new FileInputStream("/var/www/files/index.txt");
        response.getOutputStream().write(in.read());
        in.close();
    }
}
