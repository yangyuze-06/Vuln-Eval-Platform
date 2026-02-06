/**
 * OWASP Benchmark v1.2
 *
 * <p>This file is part of the Open Web Application Security Project (OWASP) Benchmark Project. For
 * details, please see <a
 * href="https://owasp.org/www-project-benchmark/">https://owasp.org/www-project-benchmark/</a>.
 *
 * <p>The OWASP Benchmark is free software: you can redistribute it and/or modify it under the terms
 * of the GNU General Public License as published by the Free Software Foundation, version 2.
 *
 * <p>The OWASP Benchmark is distributed in the hope that it will be useful, but WITHOUT ANY
 * WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
 * PURPOSE. See the GNU General Public License for more details.
 *
 * @author Dave Wichers
 * @created 2015
 */
package org.owasp.benchmark.testcode;

import java.io.IOException;
import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

@WebServlet(value = "/pathtraver-00/BenchmarkTest00001")
public class BenchmarkTest00001 extends HttpServlet {

    private static final long serialVersionUID = 1L;

    @Override
    public void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        response.setContentType("text/html;charset=UTF-8");
        javax.servlet.http.Cookie userCookie =
                new javax.servlet.http.Cookie("BenchmarkTest00001", "FileName");
        userCookie.setMaxAge(60 * 3); // Store cookie for 3 minutes
        userCookie.setSecure(true);
        userCookie.setPath(request.getRequestURI());
        userCookie.setDomain(new java.net.URL(request.getRequestURL().toString()).getHost());
        response.addCookie(userCookie);
        javax.servlet.RequestDispatcher rd =
                request.getRequestDispatcher("/pathtraver-00/BenchmarkTest00001.html");
        rd.include(request, response);
    }

    @Override
    public void doPost(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {

        // ===== [准备阶段] =====
        response.setContentType("text/html;charset=UTF-8");

        // ===== [SOURCE 起点：从请求读取 Cookie（攻击者可控入口）] =====
        javax.servlet.http.Cookie[] theCookies = request.getCookies();
        // ↑ SOURCE(候选)：请求头携带的 Cookie，客户端可控

        String param = "noCookieValueSupplied";
        // ↑ 初始是安全常量（untainted default）

        if (theCookies != null) {
            for (javax.servlet.http.Cookie theCookie : theCookies) {

                // ===== [定位目标 Cookie 名称] =====
                if (theCookie.getName().equals("BenchmarkTest00001")) {

                    // ===== [SOURCE 确认：取 Cookie 的 value] =====
                    param = java.net.URLDecoder.decode(theCookie.getValue(), "UTF-8");
                    // ↑ SOURCE：theCookie.getValue() 是攻击者可控数据
                    // ↑ URLDecoder.decode 不是净化器，只是“解码”（taint 仍然存在）

                    break;
                }
            }
        }

        String fileName = null;
        java.io.FileInputStream fis = null;

        try {
            // ===== [FLOW：污点传播（字符串拼接）] =====
            fileName = org.owasp.benchmark.helpers.Utils.TESTFILES_DIR + param;
            // ↑ FLOW：param(tainted) -> fileName(tainted)
            // ↑ 这不是净化（sanitizer），只是拼接路径前缀

            // ===== [SINK：危险点（以 tainted 路径打开文件）] =====
            fis = new java.io.FileInputStream(new java.io.File(fileName));
            // ↑ SINK：FileInputStream(File) 读取文件
            // ↑ 若 fileName 含 ../ 等，可导致 Path Traversal / 任意文件读取风险

            byte[] b = new byte[1000];
            int size = fis.read(b);

            // ===== [输出阶段] =====
            response.getWriter()
                    .println(
                            "The beginning of file: '"
                                    + org.owasp.esapi.ESAPI.encoder().encodeForHTML(fileName)
                                    + "' is:\n\n"
                                    + org.owasp
                                            .esapi
                                            .ESAPI
                                            .encoder()
                                            .encodeForHTML(new String(b, 0, size)));

            // 注意：encodeForHTML 只是在“输出到 HTML 时做编码”，
            // 它对“文件路径是否安全”没有帮助，所以不算 Sanitizer。

        } catch (Exception e) {
            // 异常处理与污点分析主链路无关（不影响 source→sink 是否成立）
            System.out.println("Couldn't open FileInputStream on file: '" + fileName + "'");
            response.getWriter()
                    .println(
                            "Problem getting FileInputStream: "
                                    + org.owasp
                                            .esapi
                                            .ESAPI
                                            .encoder()
                                            .encodeForHTML(e.getMessage()));
        } finally {
            // 资源关闭，与漏洞是否存在无关
            if (fis != null) {
                try {
                    fis.close();
                    fis = null;
                } catch (Exception e) {
                    // we tried...
                }
            }
        }
    }
}

// CWE-22
