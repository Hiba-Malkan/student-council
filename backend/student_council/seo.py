from django.http import HttpRequest, HttpResponse


def absolute_url(request: HttpRequest, path: str) -> str:
    return request.build_absolute_uri(path)


def robots_txt(request: HttpRequest) -> HttpResponse:
    lines = [
        "User-agent: *",
        "Allow: /",
        "",
        "Disallow: /admin/",
        "Disallow: /api/",
        "Disallow: /dashboard/",
        "Disallow: /profile/",
        "Disallow: /notifications/",
        "Disallow: /feedback/",
        "Disallow: /contact-messages/",
        "Disallow: /meetings/",
        "Disallow: /duties/",
        "Disallow: /duty-roster/",
        "Disallow: /gatepass/",
        "Disallow: /discipline/",
        "Disallow: /announcements/new/",
        "Disallow: /announcements/edit/",
        "",
        f"Sitemap: {absolute_url(request, '/sitemap.xml')}",
        "",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def sitemap_xml(request: HttpRequest) -> HttpResponse:
    urls = [
        {"loc": "/", "priority": "1.0", "changefreq": "daily"},
        {"loc": "/about/", "priority": "0.9", "changefreq": "monthly"},
        {"loc": "/announcements/", "priority": "0.8", "changefreq": "weekly"},
        {"loc": "/clubs/", "priority": "0.8", "changefreq": "weekly"},
        {"loc": "/competitions/", "priority": "0.8", "changefreq": "weekly"},
        {"loc": "/contact-admin/", "priority": "0.5", "changefreq": "yearly"},
    ]
    entries = "\n".join(
        "  <url>\n"
        f"    <loc>{absolute_url(request, item['loc'])}</loc>\n"
        f"    <changefreq>{item['changefreq']}</changefreq>\n"
        f"    <priority>{item['priority']}</priority>\n"
        "  </url>"
        for item in urls
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n"
        "</urlset>\n"
    )
    return HttpResponse(xml, content_type="application/xml")