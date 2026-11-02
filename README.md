# Mikayel Tovmasyan — academic website

A lightweight academic website for [mikayel-tovmasyan.github.io](https://mikayel-tovmasyan.github.io), presenting research and teaching with equal prominence. It uses ordinary HTML and shared CSS, with no JavaScript, third-party fonts, analytics, framework, package installation or build step. Abstracts expand using native HTML `<details>` elements.

The academic content and downloadable PDF are based on the authoritative CV, version 38, dated **November 2, 2026**. Original CV sources, reference CVs and private working materials are kept outside this repository.

## View locally

Open `index.html` in a browser. The four main pages, images, styling and CV use relative links and work directly from disk. The `404.html` page deliberately uses root-relative links so it also works for nested missing URLs on GitHub Pages; preview it through a local server.

For an HTTP preview, open a terminal in this repository and run:

```sh
python -m http.server 8000 --bind 127.0.0.1
```

Then open [http://127.0.0.1:8000/](http://127.0.0.1:8000/). Stop the server with Ctrl+C. If `python` is unavailable or opens a store prompt, use your installed Python 3 executable instead; on Windows the launcher may be `py -3`, and on other systems it may be `python3`. The optional check script requires Python 3.10 or later.

## File guide

| File | Purpose |
| --- | --- |
| `index.html` | Introduction, affiliation, research and teaching highlights |
| `research.html` | Job-market paper, working papers, projects and expandable abstracts |
| `teaching.html` | Teaching responsibilities, courses, supervision and award |
| `cv.html` | CV download, education and appointments |
| `404.html` | Friendly missing-page screen |
| `assets/site.css` | Shared colors, typography, spacing and responsive layouts |
| `assets/favicon.svg` | Browser icon |
| `assets/mikayel-tovmasyan.jpg` | Supplied portrait |
| `assets/Mikayel_Tovmasyan_CV.pdf` | Public CV at a stable download address |
| `sitemap.xml`, `robots.txt` | Search-engine discovery |
| `.nojekyll` | Serves the static files without Jekyll processing |
| `scripts/check_site.py` | Local structure, link, asset and optional HTTP checks |

## Update content

- **CV:** replace `assets/Mikayel_Tovmasyan_CV.pdf` with the approved current PDF, retaining the filename. Update the `?v=` query on every CV link in the HTML pages when replacing the PDF so browsers request the current file. Do not edit the original CV through this repository. Update the date and page count in `cv.html`, its description and Open Graph description in `<head>`, any changed education/appointment summaries, and the provenance date in this README.
- **Research:** edit `research.html` and corresponding homepage highlights. Preserve the distinction between published, revise-and-resubmit, working-paper and work-in-progress statuses. Check journal names and coauthors against the authoritative record. Keep the job-market paper's `<summary>` and abstract inside its `<details>` element. Other paper descriptions are displayed directly below their titles and coauthors using `<p class="paper-description">`. Use actual abstracts and public paper links; add local paper PDFs only when approved for release.
- **Teaching:** edit the course records in `teaching.html`, retaining institution, degree level, dates and exact responsibility. Distinguish independent teaching, co-teaching, tutorials and supervision. Update homepage highlights when relevant. Add evaluations or student material only if appropriate for public release.
- **Shared information:** navigation, contact details and footers are repeated in the HTML files. Apply shared changes consistently, retaining the correct `aria-current="page"` link on each main page. Keep the 404 links root-relative.
- **Dates and metadata:** update each changed page's visible footer date, relevant `<title>`, description and Open Graph metadata. Set that page's `<lastmod>` in `sitemap.xml` to its actual substantive revision date (`YYYY-MM-DD`). Keep canonical URLs, Open Graph URLs and sitemap addresses aligned if a page URL changes.
- **Appearance:** adjust shared styles in `assets/site.css`. Retain keyboard focus styles, readable contrast, image alternative text and the skip link. Check both desktop and narrow mobile layouts after changes.
- **Portrait:** `assets/mikayel-tovmasyan.jpg` is the optimized website copy of the supplied `Profile photo_Slack.png`. Keep original photos local and ignored by Git. When replacing the portrait, update its intrinsic width and height and the `?v=` version in `index.html` so browsers load the new copy promptly.

## Check changes

From the repository root:

```sh
python scripts/check_site.py
```

With the preview server running, also run:

```sh
python scripts/check_site.py --base-url http://127.0.0.1:8000/
```

The script checks page metadata and landmarks, duplicate IDs, accessible link text, image alt attributes, local destinations/fragments, PDF signatures and, optionally, HTTP responses and content types. It does not validate academic claims, external-link availability or every accessibility requirement. Manually check navigation, keyboard focus, abstract expansion, portrait layout, CV download and paper links. Inspect mobile layouts for clipping. A basic Python server does not automatically serve the custom 404 page for missing URLs; open `/404.html` to preview its appearance and test real missing URLs after deployment.

## Publish only after explicit approval

The local version must be reviewed and explicitly approved before committing and pushing it for publication.

1. Review changed files and the public CV for accuracy and personal information. Stage only approved website files; keep source documents, private materials and review outputs out of the repository.
2. Confirm the existing `origin` remote is the intended repository. Commit the reviewed changes on `main`, then push `main` to that remote. Do not force-push.
3. Inspect **Settings → Pages** on GitHub. Existing remote settings have not been assumed. Preserve a working configuration. If Pages is unconfigured, choose **Deploy from a branch**, select **main** and **/(root)**, then save. This matches [GitHub's branch publishing guidance](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site). Keep `.nojekyll`; see [GitHub's static-site instructions](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site).
4. Check the deployment result in GitHub Actions/Pages, then visit [the HTTPS website](https://mikayel-tovmasyan.github.io). Verify all four pages, portrait, abstracts, PDF download, external paper links and a deliberately nonexistent URL. Check HTTPS enforcement in Pages settings when available and inspect desktop and mobile views again.

## Design references

The design is original. Academic conventions and functionality were informed by [Coly Elhai](https://celhai.github.io/), [Sebastian Ernst](https://seb-ernst.github.io/), [Chloé de Meulenaer](https://chloedemeulenaer.github.io/), [Clara von Bismarck-Osten](https://claravobi.github.io/), [Ian Sapollnik](https://isapollnik.github.io/) and [Dustin Swonder](https://dustinswonder.github.io/).

Professional guidance: [University of Maryland Economics — Job Market Candidate Websites](https://wiki.econ.umd.edu/job_market_candidates); [European University Institute Economics — Job Market Procedures](https://www.eui.eu/en/academic-units/department-of-economics/job-market/procedures); Harvard University Office of Career Services, *GSAS: CVs and Cover Letters* (2019). These references informed clear navigation, accessible papers and CV, concise professional information and substantive teaching evidence; their documents and content are not redistributed here.
