// Negative CWE-089 cases: SQL execution uses constants or parameter binding.
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.Statement;
import javax.servlet.http.HttpServletRequest;

class SqlInjectionNegative {
    void constantStatement(Connection conn) throws Exception {
        Statement stmt = conn.createStatement();
        stmt.executeQuery("select * from users where active = 1");
    }

    void parameterizedPreparedStatement(Connection conn, HttpServletRequest request) throws Exception {
        String id = request.getParameter("id");
        PreparedStatement ps = conn.prepareStatement("select * from users where id = ?");
        ps.setString(1, id);
        ps.executeQuery();
    }
}
