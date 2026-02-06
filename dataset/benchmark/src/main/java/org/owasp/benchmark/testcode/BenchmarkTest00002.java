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

@WebServlet(value = "/pathtraver-00/BenchmarkTest00002")
public class BenchmarkTest00002 extends HttpServlet {

    private static final long serialVersionUID = 1L;

    @Override
    public void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {
        response.setContentType("text/html;charset=UTF-8");
        javax.servlet.http.Cookie userCookie =
                new javax.servlet.http.Cookie("BenchmarkTest00002", "FileName");
        userCookie.setMaxAge(60 * 3); // Store cookie for 3 minutes
        userCookie.setSecure(true);
        userCookie.setPath(request.getRequestURI());
        userCookie.setDomain(new java.net.URL(request.getRequestURL().toString()).getHost());
        response.addCookie(userCookie);
        javax.servlet.RequestDispatcher rd =
                request.getRequestDispatcher("/pathtraver-00/BenchmarkTest00002.html");
        rd.include(request, response);
    }

    // ============================================================
    // CWE-22: Path Traversal（路径遍历）
    // Case: OWASP BenchmarkTest00001
    // ============================================================
    //
    // 漏洞本质：
    // 攻击者可控输入 → 构造文件路径 → 进入文件系统 API
    // 若未进行路径规范化 / 白名单校验 → 可访问任意文件
    //
    // ============================================================

    @Override
    public void doPost(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {

        // ===== [准备阶段] =====
        response.setContentType("text/html;charset=UTF-8");
        // ↑ 与污点分析无关（环境设置）

        // =========================================================
        // ===== [SOURCE 起点：攻击者可控输入] =====
        // =========================================================

        javax.servlet.http.Cookie[] theCookies = request.getCookies();
        // ↑ SOURCE 候选：
        // Cookie 来自 HTTP 请求头，完全可由客户端伪造
        // 属于「非参数型输入源」，但仍是 attacker-controlled

        String param = "noCookieValueSupplied";
        // ↑ 初始值为安全常量（untainted）

        if (theCookies != null) {
            for (javax.servlet.http.Cookie theCookie : theCookies) {

                // ===== [定位目标 Cookie] =====
                if (theCookie.getName().equals("BenchmarkTest00001")) {

                    // ===== [SOURCE 确认：读取 Cookie 的值] =====
                    param = java.net.URLDecoder.decode(theCookie.getValue(), "UTF-8");
                    // ↑ SOURCE：
                    // theCookie.getValue() 为攻击者可控数据
                    //
                    // ↑ 注意：
                    // URLDecoder.decode 只是“解码”，不是净化（Sanitizer）
                    // 污点（taint）在此不会被清除

                    break;
                }
            }
        }

        // =========================================================
        // ===== [FLOW：污点传播] =====
        // =========================================================

        String fileName = null;
        java.io.FileInputStream fis = null;

        try {

            // ===== [FLOW：路径拼接] =====
            fileName = org.owasp.benchmark.helpers.Utils.TESTFILES_DIR + param;
            // ↑ FLOW：
            // param (tainted) → fileName (tainted)
            //
            // ↑ 关键点：
            // 仅拼接固定目录前缀 ≠ 安全
            // 若 param 含 "../"，仍可逃逸 TESTFILES_DIR

            // =====================================================
            // ===== [SINK：危险点（文件系统访问）] =====
            // =====================================================

            fis = new java.io.FileInputStream(new java.io.File(fileName));
            // ↑ SINK：
            // FileInputStream(File) 是文件系统读取 API
            //
            // ↑ 漏洞触发条件：
            // tainted 路径 → FileInputStream
            //
            // ↑ 危害：
            // 攻击者可构造 "../" 等路径，读取任意系统文件
            // → CWE-22 Path Traversal

            byte[] b = new byte[1000];
            int size = fis.read(b);

            // =====================================================
            // ===== [输出阶段（与漏洞无关）] =====
            // =====================================================

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

            // ↑ 注意：
            // encodeForHTML 是“输出编码”
            // 仅防止 XSS，不影响文件路径解析
            // 因此 ❌ 不是 Sanitizer

        } catch (Exception e) {

            // 异常处理不影响污点是否到达 Sink
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

            // 资源释放与漏洞无关
            if (fis != null) {
                try {
                    fis.close();
                    fis = null;
                } catch (Exception e) {
                    // ignore
                }
            }
        }
    }
}
