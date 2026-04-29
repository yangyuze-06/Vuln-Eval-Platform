// Negative test case for CWE-090 LDAP Injection.
// LDAP search uses a constant filter instead of user-controlled input.
package cwe090;

import javax.naming.NamingException;
import javax.naming.directory.DirContext;
import javax.naming.directory.SearchControls;
import javax.servlet.http.HttpServletRequest;

public class LdapInjectionNegative {
    public void search(HttpServletRequest request, DirContext context) throws NamingException {
        request.getParameter("user");
        String filter = "(uid=service-account)";
        SearchControls controls = new SearchControls();

        context.search("ou=people,dc=example,dc=com", filter, controls);
    }
}
