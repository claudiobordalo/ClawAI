from __future__ import annotations

import requests


class WebSearch:

    USER_AGENT = (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/137.0 Safari/537.36"
    )

    def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[dict]:

        response = requests.get(
            "https://duckduckgo.com/html/",
            params={
                "q": query
            },
            headers={
                "User-Agent": self.USER_AGENT
            },
            timeout=30,
        )

        response.raise_for_status()

        html = response.text

        results = []

        start = 0

        while len(results) < limit:

            index = html.find(
                'class="result__a"',
                start,
            )

            if index == -1:
                break

            href = html.find(
                'href="',
                index,
            )

            href_end = html.find(
                '"',
                href + 6,
            )

            title_start = html.find(
                ">",
                href_end,
            ) + 1

            title_end = html.find(
                "</a>",
                title_start,
            )

            title = (
                html[title_start:title_end]
                .replace("<b>", "")
                .replace("</b>", "")
                .strip()
            )

            url = html[href + 6:href_end]

            results.append(
                {
                    "title": title,
                    "url": url,
                }
            )

            start = title_end

        return results


web = WebSearch()
