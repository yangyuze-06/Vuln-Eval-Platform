// Minimal probe to verify whether the local Sparrow build resolves JDK +
// third-party (servlet) types to fully-qualified names. Build this single file
// into a throwaway DB, then query reference_type. See repro commands in
// reports/codefuse-db-mac-linux-rootcause-v2.md (section 11).
import java.util.List;
import javax.servlet.http.HttpServletRequest;

class Mini {
    void f(HttpServletRequest req, List<String> xs) {
        String s = req.getParameter("x");   // source: javax.servlet
        int n = xs.size();                   // relay: java.util.List
        boolean b = s.startsWith("../");     // relay: java.lang.String
        StringBuilder sb = new StringBuilder();
        sb.append(s);                        // relay: java.lang.StringBuilder
        try {
            Runtime.getRuntime().exec(sb.toString());  // sink: java.lang.Runtime
        } catch (Exception e) {
            // ignore
        }
    }
}
