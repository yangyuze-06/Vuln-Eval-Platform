// Positive CWE-089 cases: tainted request data reaches SQL execution sinks.
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.Statement;
import javax.servlet.http.HttpServletRequest;

class SqlInjectionPositive {
    void statementExecuteQuery(Connection conn, HttpServletRequest request) throws Exception {
        String id = request.getParameter("id");
        Statement stmt = conn.createStatement();
        stmt.executeQuery("select * from users where id = " + id);
    }

    void chainedCreateStatement(Connection conn, HttpServletRequest request) throws Exception {
        String name = request.getParameter("name");
        conn.createStatement().execute("select * from users where name = '" + name + "'");
    }

    void preparedStatementWithConcatenation(Connection conn, HttpServletRequest request) throws Exception {
        String role = request.getParameter("role");
        PreparedStatement ps = conn.prepareStatement("select * from users where role = '" + role + "'");
        ps.executeQuery();
    }
}
